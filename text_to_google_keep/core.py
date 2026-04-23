"""Shared Google Keep import logic (CLI and web)."""

from __future__ import annotations

import getpass
from collections.abc import Iterable
from pathlib import Path

import gkeepapi
import gkeepapi.exception as gexc
import keyring

KEYRING_SERVICE = "text-to-google-keep"


class KeepUserError(Exception):
    """Recoverable user-facing error (auth, validation, API)."""


def _token_key(email: str) -> str:
    return email.strip().lower()


def load_token(email: str) -> str | None:
    return keyring.get_password(KEYRING_SERVICE, _token_key(email))


def save_token(email: str, token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, _token_key(email), token)


def clear_token(email: str) -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, _token_key(email))
    except keyring.errors.PasswordDeleteError:
        pass


def attach_label(keep: gkeepapi.Keep, note, name: str) -> None:
    name = (name or "").strip()
    if not name:
        return
    try:
        keep.createLabel(name)
    except gexc.LabelException as e:
        if str(e) != "Label exists":
            raise
    label = keep.findLabel(name)
    if label is None:
        raise KeepUserError(f"Could not resolve label: {name!r}")
    note.labels.add(label)


def login_keep(
    email: str,
    *,
    reset: bool = False,
    master_token: str | None = None,
    password: str | None = None,
    prompt_password: bool = False,
) -> tuple[gkeepapi.Keep, bool]:
    """Authenticate to Keep. Token from argument overrides keyring.
    Returns (keep, saved_new_token_to_keyring).
    """
    if reset:
        clear_token(email)
    email = email.strip()
    keep = gkeepapi.Keep()
    explicit = (master_token or "").strip()
    token = explicit or load_token(email)
    if token:
        try:
            keep.authenticate(email, token)
        except gexc.LoginException as e:
            raise KeepUserError(
                "Saved token failed: "
                + str(e)
                + "\nTry: text-to-google-keep --reset ... then sign in again, or pass --token."
            ) from e
        return keep, False

    if password is None and prompt_password:
        password = getpass.getpass("Google password (or App Password if 2SV is on): ")
    if not password:
        raise KeepUserError("Google password or master token is required.")

    try:
        keep.login(email, password)
    except gexc.BrowserLoginRequiredException as e:
        url = getattr(e, "url", "") or ""
        raise KeepUserError(
            "Google wants browser verification. Open:\n"
            + url
            + "\nThen obtain a master token (see README) and run with --token."
        ) from e
    except gexc.LoginException as e:
        raise KeepUserError(
            "Sign-in failed: "
            + str(e)
            + "\nWith 2-Step Verification, use a Google App Password here, or use --token."
        ) from e
    t = keep.getMasterToken()
    saved = bool(t and not explicit)
    if saved:
        save_token(email, t)
    return keep, saved


def import_lines(
    keep: gkeepapi.Keep,
    lines: Iterable[str],
    labels: list[str],
    blank: bool,
) -> tuple[int, int]:
    """Import each non-blank line as a note. Returns (imported_count, skipped_blank)."""
    count = 0
    skipped = 0
    for raw in lines:
        line = raw.rstrip("\n\r")
        if not blank and not line.strip():
            skipped += 1
            continue
        note = keep.createNote(None, line)
        for lab in labels:
            attach_label(keep, note, lab)
        count += 1
    keep.sync()
    return count, skipped


def import_lines_from_path(
    keep: gkeepapi.Keep,
    path: Path,
    labels: list[str],
    blank: bool,
) -> tuple[int, int]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return import_lines(keep, f, labels, blank)


def parse_labels_csv(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").replace("\n", ",").split(",") if p.strip()]
