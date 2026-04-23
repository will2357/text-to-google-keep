"""Google OAuth + official Keep REST API (personal Google accounts)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import keyring
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from text_to_google_keep.core import KeepUserError

SCOPES = ("https://www.googleapis.com/auth/keep",)
KEYRING_OAUTH_SERVICE = "text-to-google-keep-oauth"


def oauth_keyring_account(email: str) -> str:
    return email.strip().lower()


def load_oauth_json(email: str) -> str | None:
    return keyring.get_password(KEYRING_OAUTH_SERVICE, oauth_keyring_account(email))


def save_oauth_json(email: str, blob: str) -> None:
    keyring.set_password(KEYRING_OAUTH_SERVICE, oauth_keyring_account(email), blob)


def clear_oauth(email: str) -> None:
    try:
        keyring.delete_password(KEYRING_OAUTH_SERVICE, oauth_keyring_account(email))
    except keyring.errors.PasswordDeleteError:
        pass


def resolve_client_secrets_path(explicit: str | None) -> Path:
    p = explicit or os.environ.get("GOOGLE_KEEP_CLIENT_SECRETS") or os.environ.get("GOOGLE_CLIENT_SECRETS")
    if p:
        return Path(p).expanduser().resolve()
    return (Path.cwd() / "client_secret.json").resolve()


def fetch_google_email(creds: Credentials) -> str:
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise KeepUserError(f"Could not read Google profile: HTTP {e.code}") from e
    except OSError as e:
        raise KeepUserError(f"Could not read Google profile: {e}") from e
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise KeepUserError("Google account has no email in userinfo response.")
    return email


def _creds_from_json(blob: str) -> Credentials:
    info = json.loads(blob)
    return Credentials.from_authorized_user_info(info, list(SCOPES))


def _refresh_and_persist(email: str, creds: Credentials) -> Credentials:
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_oauth_json(email, creds.to_json())
    return creds


def oauth_credentials_cli(
    client_secrets: Path,
    *,
    email: str | None,
    reset: bool,
) -> tuple[Credentials, str]:
    """Installed-app OAuth (browser opens). Persists refresh token under discovered or given email."""
    if not client_secrets.is_file():
        raise KeepUserError(
            f"OAuth client secrets file not found: {client_secrets}\n"
            "Set GOOGLE_KEEP_CLIENT_SECRETS or pass --client-secrets (see README: Google OAuth)."
        )
    em = (email or "").strip().lower()
    if reset and em:
        clear_oauth(em)
    if em:
        blob = load_oauth_json(em) if not reset else None
        if blob:
            creds = _refresh_and_persist(em, _creds_from_json(blob))
            return creds, em

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), list(SCOPES))
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    actual = fetch_google_email(creds)
    if em and actual != em:
        raise KeepUserError(f"Signed in as {actual}, but expected {em} (--email / GOOGLE_EMAIL).")
    save_oauth_json(actual, creds.to_json())
    return creds, actual


def oauth_flow_for_redirect(client_secrets: Path, redirect_uri: str) -> Flow:
    return Flow.from_client_secrets_file(str(client_secrets), scopes=list(SCOPES), redirect_uri=redirect_uri)


def oauth_authorization_url(flow: Flow) -> tuple[str, str]:
    url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    return url, state


def build_keep_service(creds: Credentials) -> Any:
    return build("keep", "v1", credentials=creds, cache_discovery=False)


def import_lines_rest(service: Any, lines: Iterable[str], blank: bool) -> tuple[int, int]:
    """Create one text note per line via keep.googleapis.com (no labels — API has no label resource)."""
    count = 0
    skipped = 0
    for raw in lines:
        line = raw.rstrip("\n\r")
        if not blank and not line.strip():
            skipped += 1
            continue
        text = line if len(line) <= 20_000 else line[:20_000]
        note: dict[str, Any] = {"title": "", "body": {"text": {"text": text}}}
        try:
            service.notes().create(body=note).execute()
        except HttpError as e:
            raise KeepUserError(_format_http_error(e)) from e
        count += 1
    return count, skipped


def import_lines_rest_from_path(service: Any, path: Path, blank: bool) -> tuple[int, int]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return import_lines_rest(service, f, blank)


def _format_http_error(e: HttpError) -> str:
    try:
        body = e.content.decode(errors="replace")[:4000]
    except Exception:
        body = str(e)
    return (
        f"Keep API HTTP {e.resp.status}: {body}\n"
        "Enable **Google Keep API** for your Cloud project and add your Google account as a "
        "**test user** on the OAuth consent screen while the app is in Testing (see README)."
    )


def oauth_credentials_web_saved(email: str, *, reset: bool) -> Credentials:
    """Load refresh token from keyring (web import after browser sign-in)."""
    if reset:
        clear_oauth(email)
    blob = load_oauth_json(email)
    if not blob:
        raise KeepUserError(
            "No Google OAuth token for this email. Open **Sign in with Google** in the header first."
        )
    return _refresh_and_persist(email, _creds_from_json(blob))
