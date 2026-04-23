"""Local web UI for pasting or uploading lines into Google Keep."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from text_to_google_keep.core import KeepUserError, import_lines, login_keep, parse_labels_csv


def create_app() -> Flask:
    root = Path(__file__).resolve().parent
    app = Flask(__name__, template_folder=str(root / "templates"))
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "text-to-google-keep-dev")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/")
    def submit():
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
