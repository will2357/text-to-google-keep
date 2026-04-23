"""CLI: one Google Keep note per line of a UTF-8 text file."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from text_to_google_keep.core import KeepUserError, import_lines_from_path, login_keep
from text_to_google_keep.oauth_keep import (
    build_keep_service,
    import_lines_rest_from_path,
    oauth_credentials_cli,
    resolve_client_secrets_path,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--email", envvar="GOOGLE_EMAIL", help="Google account email (or set GOOGLE_EMAIL).")
@click.option(
    "--token",
    envvar="KEEP_MASTER_TOKEN",
    help="Master token (aas_et/...) for gkeepapi; skips keyring password flow.",
)
@click.option(
    "--label", "-l", "labels", multiple=True, help="Keep label on every note (gkeepapi only; not supported with --oauth).",
)
@click.option(
    "--blank-lines/--no-blank-lines",
    default=False,
    help="Import blank / whitespace-only lines as empty notes.",
)
@click.option("--reset", is_flag=True, help="Forget saved gkeepapi master token for this email in the keyring.")
@click.option(
    "--oauth",
    is_flag=True,
    help="Use Google OAuth (consent screen) + official Keep API — works for typical personal Google accounts.",
)
@click.option(
    "--client-secrets",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    envvar="GOOGLE_KEEP_CLIENT_SECRETS",
    default=None,
    help="Path to OAuth client secrets JSON (or set GOOGLE_KEEP_CLIENT_SECRETS). Required on first --oauth login.",
)
@click.option("--reset-oauth", is_flag=True, help="Forget saved OAuth credentials for this email before sign-in.")
def cli(
    file: Path,
    email: str | None,
    token: str | None,
    labels: tuple[str, ...],
    blank_lines: bool,
    reset: bool,
    oauth: bool,
    client_secrets: Path | None,
    reset_oauth: bool,
) -> None:
    """Create one Google Keep note per line of FILE (UTF-8)."""
    label_list = [x.strip() for x in labels if x.strip()]
    if oauth and token:
        raise click.ClickException("Use either --oauth or --token, not both.")
    if oauth and label_list:
        raise click.ClickException("Official Keep API has no label support; omit --label when using --oauth.")

    if oauth:
        if reset_oauth and not (email or "").strip():
            raise click.ClickException("--reset-oauth requires --email or GOOGLE_EMAIL.")
        secrets = client_secrets or resolve_client_secrets_path(None)
        if not secrets.is_file():
            raise click.ClickException(
                f"Missing OAuth client secrets file: {secrets}\n"
                "Download JSON from Google Cloud Console (OAuth client) and set "
                "--client-secrets or GOOGLE_KEEP_CLIENT_SECRETS (see README: Google OAuth)."
            )
        em = (email or "").strip() or None
        try:
            creds, account = oauth_credentials_cli(secrets, email=em, reset=reset_oauth)
            service = build_keep_service(creds)
        except KeepUserError as e:
            raise click.ClickException(str(e)) from e
        except Exception as e:
            raise click.ClickException(repr(e)) from e
        try:
            n, skipped = import_lines_rest_from_path(service, file, blank_lines)
        except KeepUserError as e:
            raise click.ClickException(str(e)) from e
        except Exception as e:
            raise click.ClickException(f"Import failed: {e!r}") from e
        if skipped:
            click.echo(f"Skipped {skipped} blank line(s).")
        click.echo(f"Imported {n} note(s) from {file} via Google OAuth ({account}).")
        return

    if not email:
        email = click.prompt("Google email")
    email = email.strip()
    try:
        keep, saved = login_keep(
            email,
            reset=reset,
            master_token=token,
            password=None,
            prompt_password=True,
        )
        if saved:
            click.echo("Master token saved to your OS keyring for next runs.")
    except KeepUserError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        raise click.ClickException(repr(e)) from e
    try:
        n, skipped = import_lines_from_path(keep, file, label_list, blank=blank_lines)
    except Exception as e:
        raise click.ClickException(f"Import failed: {e!r}") from e
    if skipped:
        click.echo(f"Skipped {skipped} blank line(s).")
    click.echo(f"Imported {n} note(s) from {file}.")


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except click.ClickException as e:
        click.echo(e.format_message(), err=True)
        sys.exit(1)
