"""Local web UI for pasting or uploading lines into Google Keep."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from google_auth_oauthlib.flow import Flow

from text_to_google_keep.core import KeepUserError, import_lines, login_keep, parse_labels_csv
from text_to_google_keep.oauth_keep import (
    SCOPES,
    build_keep_service,
    fetch_google_email,
    import_lines_rest,
    oauth_authorization_url,
    oauth_credentials_web_saved,
    oauth_flow_for_redirect,
    resolve_client_secrets_path,
    save_oauth_json,
)


def create_app() -> Flask:
    root = Path(__file__).resolve().parent
    app = Flask(__name__, template_folder=str(root / "templates"))
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "text-to-google-keep-dev")

    def _oauth_redirect_uri() -> str:
        return url_for("oauth_callback", _external=True)

    @app.get("/")
    def index():
        oauth_ready = resolve_client_secrets_path(None).is_file()
        return render_template("index.html", oauth_ready=oauth_ready)

    @app.get("/oauth/start")
    def oauth_start():
        path = resolve_client_secrets_path(None)
        if not path.is_file():
            flash(
                "OAuth client secrets file not found. Set GOOGLE_KEEP_CLIENT_SECRETS or place "
                "client_secret.json in the current working directory (see README: Google OAuth).",
                "error",
            )
            return redirect(url_for("index"))
        redirect_uri = _oauth_redirect_uri()
        flow = oauth_flow_for_redirect(path, redirect_uri)
        url, state = oauth_authorization_url(flow)
        session["oauth_state"] = state
        session["oauth_code_verifier"] = flow.code_verifier
        session["oauth_redirect_uri"] = redirect_uri
        session["oauth_secrets_path"] = str(path)
        return redirect(url)

    @app.get("/oauth/callback")
    def oauth_callback():
        if request.args.get("error"):
            flash(f"Google OAuth error: {request.args.get('error_description', request.args.get('error'))}", "error")
            return redirect(url_for("index"))
        path_s = session.get("oauth_secrets_path")
        redirect_uri = session.get("oauth_redirect_uri")
        st = session.get("oauth_state")
        verifier = session.get("oauth_code_verifier")
        if not path_s or not redirect_uri or not st:
            flash("OAuth session expired; start sign-in again.", "error")
            return redirect(url_for("index"))
        if request.args.get("state") != st:
            flash("Invalid OAuth state; try signing in again.", "error")
            return redirect(url_for("index"))
        path = Path(path_s)
        email: str | None = None
        try:
            flow = Flow.from_client_secrets_file(
                str(path),
                scopes=list(SCOPES),
                redirect_uri=redirect_uri,
                state=st,
                code_verifier=verifier,
            )
            flow.fetch_token(authorization_response=request.url)
            creds = flow.credentials
            email = fetch_google_email(creds)
            save_oauth_json(email, creds.to_json())
        except Exception as e:
            flash(f"OAuth failed: {e!r}", "error")
            return redirect(url_for("index"))
        finally:
            session.pop("oauth_state", None)
            session.pop("oauth_code_verifier", None)
            session.pop("oauth_redirect_uri", None)
            session.pop("oauth_secrets_path", None)

        flash(f"Signed in with Google as {email}. Enable **Use Google OAuth** on import.", "ok")
        return redirect(url_for("index"))

    @app.post("/")
    def submit():
        use_oauth = request.form.get("use_oauth") == "1"
        email = (request.form.get("email") or "").strip()
        if not email:
            flash("Email is required.", "error")
            return redirect(url_for("index"))
        password = (request.form.get("password") or "").strip() or None
        master_token = (request.form.get("master_token") or "").strip() or None
        reset = request.form.get("reset") == "1"
        blank_lines = request.form.get("blank_lines") == "1"
        labels = parse_labels_csv(request.form.get("labels") or "")

        up = request.files.get("file")
        if up and up.filename:
            raw_text = up.read().decode("utf-8", errors="replace")
        else:
            raw_text = request.form.get("content") or ""

        if not raw_text.strip():
            flash("Paste text or choose a UTF-8 file.", "error")
            return redirect(url_for("index"))

        lines = raw_text.splitlines(keepends=True)

        if use_oauth:
            if labels:
                flash("Labels are not supported with Google OAuth (official API). Clear labels and retry.", "error")
                return redirect(url_for("index"))
            try:
                creds = oauth_credentials_web_saved(email, reset=reset)
                service = build_keep_service(creds)
                n, skipped = import_lines_rest(service, lines, blank=blank_lines)
            except KeepUserError as e:
                flash(str(e), "error")
                return redirect(url_for("index"))
            except Exception as e:
                flash(f"Import failed: {e!r}", "error")
                return redirect(url_for("index"))
            parts = [f"Imported {n} note(s) via Google OAuth."]
            if skipped:
                parts.append(f"Skipped {skipped} blank line(s).")
            flash(" ".join(parts), "ok")
            return redirect(url_for("index"))

        try:
            keep, saved = login_keep(
                email,
                reset=reset,
                master_token=master_token,
                password=password,
                prompt_password=False,
            )
            n, skipped = import_lines(keep, lines, labels, blank=blank_lines)
        except KeepUserError as e:
            flash(str(e), "error")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Import failed: {e!r}", "error")
            return redirect(url_for("index"))

        parts = [f"Imported {n} note(s)."]
        if skipped:
            parts.append(f"Skipped {skipped} blank line(s).")
        if saved:
            parts.append("Master token saved to your OS keyring.")
        flash(" ".join(parts), "ok")
        return redirect(url_for("index"))

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Web UI for text-to-google-keep (binds to localhost by default).")
    parser.add_argument("--host", default="127.0.0.1", help="Listen address (default: 127.0.0.1 only).")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
