from __future__ import annotations

from pathlib import Path

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from google_auth_oauthlib.flow import Flow
from inertia import render

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

from .models import ImportLog


def _flash_props(request):
    return [{"level": m.level_tag or "info", "text": str(m)} for m in messages.get_messages(request)]


def home(request):
    return render(
        request,
        "Home",
        props={
            "flash": _flash_props(request),
            "oauth_ready": resolve_client_secrets_path(None).is_file(),
        },
    )


@require_http_methods(["POST"])
def import_create(request):
    use_oauth = request.POST.get("use_oauth") == "true"
    email = (request.POST.get("email") or "").strip()
    if not email:
        messages.error(request, "Email is required.")
        return redirect("home")

    reset = request.POST.get("reset") == "true"
    blank_lines = request.POST.get("blank_lines") == "true"
    labels = parse_labels_csv(request.POST.get("labels") or "")

    up = request.FILES.get("file")
    if up:
        raw_text = up.read().decode("utf-8", errors="replace")
    else:
        raw_text = request.POST.get("content") or ""

    if not raw_text.strip():
        messages.error(request, "Paste text or choose a UTF-8 file.")
        return redirect("home")

    lines = raw_text.splitlines(keepends=True)

    if use_oauth:
        if labels:
            messages.error(
                request,
                "Labels are not supported with Google OAuth (official API). Clear labels and retry.",
            )
            return redirect("home")
        try:
            creds = oauth_credentials_web_saved(email, reset=reset)
            service = build_keep_service(creds)
            n, skipped = import_lines_rest(service, lines, blank=blank_lines)
        except KeepUserError as e:
            messages.error(request, str(e))
            return redirect("home")
        except Exception as e:
            messages.error(request, f"Import failed: {e!r}")
            return redirect("home")
        ImportLog.objects.create(
            email=email,
            auth_method=ImportLog.AuthMethod.OAUTH,
            lines_imported=n,
            lines_skipped=skipped,
        )
        msg = f"Imported {n} note(s) via Google OAuth."
        if skipped:
            msg += f" Skipped {skipped} blank line(s)."
        messages.success(request, msg)
        return redirect("home")

    password = (request.POST.get("password") or "").strip() or None
    master_token = (request.POST.get("master_token") or "").strip() or None
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
        messages.error(request, str(e))
        return redirect("home")
    except Exception as e:
        messages.error(request, f"Import failed: {e!r}")
        return redirect("home")

    ImportLog.objects.create(
        email=email,
        auth_method=ImportLog.AuthMethod.GKEEPAPI,
        lines_imported=n,
        lines_skipped=skipped,
    )
    parts = [f"Imported {n} note(s)."]
    if skipped:
        parts.append(f"Skipped {skipped} blank line(s).")
    if saved:
        parts.append("Master token saved to your OS keyring.")
    messages.success(request, " ".join(parts))
    return redirect("home")


def oauth_start(request):
    path = resolve_client_secrets_path(None)
    if not path.is_file():
        messages.error(
            request,
            "OAuth client secrets not found. Set GOOGLE_KEEP_CLIENT_SECRETS or add "
            "client_secret.json to the working directory.",
        )
        return redirect("home")
    redirect_uri = request.build_absolute_uri(reverse("oauth_callback"))
    flow = oauth_flow_for_redirect(path, redirect_uri)
    url, state = oauth_authorization_url(flow)
    request.session["oauth_state"] = state
    request.session["oauth_code_verifier"] = flow.code_verifier
    request.session["oauth_redirect_uri"] = redirect_uri
    request.session["oauth_secrets_path"] = str(path)
    return redirect(url)


def oauth_callback(request):
    if request.GET.get("error"):
        messages.error(
            request,
            request.GET.get("error_description") or request.GET.get("error") or "OAuth error",
        )
        return redirect("home")
    path_s = request.session.get("oauth_secrets_path")
    redirect_uri = request.session.get("oauth_redirect_uri")
    st = request.session.get("oauth_state")
    verifier = request.session.get("oauth_code_verifier")
    if not path_s or not redirect_uri or not st:
        messages.error(request, "OAuth session expired; start sign-in again.")
        return redirect("home")
    if request.GET.get("state") != st:
        messages.error(request, "Invalid OAuth state; try again.")
        return redirect("home")
    path = Path(path_s)
    signed_email: str | None = None
    try:
        flow = Flow.from_client_secrets_file(
            str(path),
            scopes=list(SCOPES),
            redirect_uri=redirect_uri,
            state=st,
            code_verifier=verifier,
        )
        auth_url = request.build_absolute_uri(request.get_full_path())
        flow.fetch_token(authorization_response=auth_url)
        creds = flow.credentials
        signed_email = fetch_google_email(creds)
        save_oauth_json(signed_email, creds.to_json())
    except Exception as e:
        messages.error(request, f"OAuth failed: {e!r}")
    else:
        messages.success(
            request,
            f"Signed in with Google as {signed_email}. Enable **Use Google OAuth** when importing.",
        )
    finally:
        request.session.pop("oauth_state", None)
        request.session.pop("oauth_code_verifier", None)
        request.session.pop("oauth_redirect_uri", None)
        request.session.pop("oauth_secrets_path", None)
    return redirect("home")
