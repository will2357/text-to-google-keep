"""CLI: one Google Keep note per line of a UTF-8 text file."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

import click
import gkeepapi
import gkeepapi.exception as gexc
import keyring

KEYRING_SERVICE = "text-to-google-keep"


def _token_key(email: str) -> str:
    return email.strip().lower()


def _load_token(email: str) -> str | None:
    return keyring.get_password(KEYRING_SERVICE, _token_key(email))


def _save_token(email: str, token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, _token_key(email), token)


def _clear_token(email: str) -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, _token_key(email))
    except keyring.errors.PasswordDeleteError:
        pass


def _attach_label(keep: gkeepapi.Keep, note, name: str) -> None:
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
        raise click.ClickException(f"Could not resolve label: {name!r}")
    note.labels.add(label)


def _login_interactive(email: str, reset: bool, master: str | None) -> gkeepapi.Keep:
    if reset:
        _clear_token(email)
    keep = gkeepapi.Keep()
    token = master or _load_token(email)
    if token:
        try:
            keep.authenticate(email, token)
        except gexc.LoginException as e:
            raise click.ClickException(
                "Saved token failed: "
                + str(e)
                + "\nTry: text-to-google-keep --reset ... then sign in again, or pass --token."
            ) from e
        return keep
    pw = getpass.getpass("Google password (or App Password if 2SV is on): ")
    try:
        keep.login(email, pw)
    except gexc.BrowserLoginRequiredException as e:
        url = getattr(e, "url", "") or ""
        raise click.ClickException(
            "Google wants browser verification. Open:\n"
            + url
            + "\nThen obtain a master token (see README) and run with --token."
        ) from e
    except gexc.LoginException as e:
        raise click.ClickException(
            "Sign-in failed: "
            + str(e)
            + "\nWith 2-Step Verification, use a Google App Password here, or use --token."
        ) from e
    t = keep.getMasterToken()
    if t and not master:
        _save_token(email, t)
        click.echo("Master token saved to your OS keyring for next runs.")
    return keep


def import_lines(
    keep: gkeepapi.Keep,
    path: Path,
    labels: list[str],
    blank: bool,
) -> int:
    count = 0
    skipped = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n\r")
            if not blank and not line.strip():
                skipped += 1
                continue
            note = keep.createNote(None, line)
            for lab in labels:
                _attach_label(keep, note, lab)
            count += 1
    keep.sync()
    if skipped:
        click.echo(f"Skipped {skipped} blank line(s).")
    return count


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--email", envvar="GOOGLE_EMAIL", help="Google account email (or set GOOGLE_EMAIL).")
@click.option(
    "--token",
    envvar="KEEP_MASTER_TOKEN",
    help="Master token (aas_et/...) instead of password; skips keyring password flow.",
)
@click.option(
    "--label", "-l", "labels", multiple=True, help="Keep label to add to every imported note (repeatable).",
)
@click.option(
    "--blank-lines/--no-blank-lines",
    default=False,
    help="Import blank / whitespace-only lines as empty notes.",
)
@click.option("--reset", is_flag=True, help="Forget saved master token for this email in the keyring.")
def cli(
    file: Path,
    email: str | None,
    token: str | None,
    labels: tuple[str, ...],
    blank_lines: bool,
    reset: bool,
) -> None:
    """Create one Google Keep note per line of FILE (UTF-8)."""
    if not email:
        email = click.prompt("Google email")
    email = email.strip()
    label_list = [x.strip() for x in labels if x.strip()]
    try:
        keep = _login_interactive(email, reset=reset, master=token)
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(repr(e)) from e
    try:
        n = import_lines(keep, file, label_list, blank=blank_lines)
    except Exception as e:
        raise click.ClickException(f"Import failed: {e!r}") from e
    click.echo(f"Imported {n} note(s) from {file}.")


def main() -> None:
    cli()


if __name__ == "__main__":
    try:
        main()
    except click.ClickException as e:
        click.echo(e.format_message(), err=True)
        sys.exit(1)
