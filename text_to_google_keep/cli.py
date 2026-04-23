"""CLI: one Google Keep note per line of a UTF-8 text file."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from text_to_google_keep.core import KeepUserError, import_lines_from_path, login_keep


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
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(repr(e)) from e
    try:
        n, skipped = import_lines_from_path(keep, file, label_list, blank=blank_lines)
    except Exception as e:
        raise click.ClickException(f"Import failed: {e!r}") from e
    if skipped:
        click.echo(f"Skipped {skipped} blank line(s).")
    click.echo(f"Imported {n} note(s) from {file}.")


def main() -> None:
    cli()


if __name__ == "__main__":
    try:
        main()
    except click.ClickException as e:
        click.echo(e.format_message(), err=True)
        sys.exit(1)
