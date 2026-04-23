from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from text_to_google_keep import cli as cli_mod


def write_sample(tmp_path: Path) -> Path:
    file = tmp_path / "notes.txt"
    file.write_text("one\ntwo\n", encoding="utf-8")
    return file


def test_cli_rejects_oauth_plus_token(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, [str(write_sample(tmp_path)), "--oauth", "--token", "x"])
    assert result.exit_code != 0
    assert "either --oauth or --token" in result.output


def test_cli_rejects_oauth_labels(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, [str(write_sample(tmp_path)), "--oauth", "-l", "A"])
    assert result.exit_code != 0
    assert "no label support" in result.output


def test_cli_oauth_happy_path(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    secrets = tmp_path / "client.json"
    secrets.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cli_mod, "oauth_credentials_cli", lambda *_a, **_kw: (SimpleNamespace(), "you@example.com"))
    monkeypatch.setattr(cli_mod, "build_keep_service", lambda _c: object())
    monkeypatch.setattr(cli_mod, "import_lines_rest_from_path", lambda *_a, **_kw: (2, 1))
    result = runner.invoke(cli_mod.cli, [str(file), "--oauth", "--client-secrets", str(secrets)])
    assert result.exit_code == 0
    assert "Skipped 1 blank line(s)." in result.output
    assert "via Google OAuth (you@example.com)" in result.output


def test_cli_oauth_missing_secrets(tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    result = runner.invoke(cli_mod.cli, [str(file), "--oauth", "--client-secrets", str(tmp_path / "none.json")])
    assert result.exit_code != 0
    assert "Invalid value for '--client-secrets'" in result.output


def test_cli_oauth_import_failure(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    secrets = tmp_path / "client.json"
    secrets.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cli_mod, "oauth_credentials_cli", lambda *_a, **_kw: (SimpleNamespace(), "you@example.com"))
    monkeypatch.setattr(cli_mod, "build_keep_service", lambda _c: object())
    monkeypatch.setattr(cli_mod, "import_lines_rest_from_path", lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("boom")))
    result = runner.invoke(cli_mod.cli, [str(file), "--oauth", "--client-secrets", str(secrets)])
    assert result.exit_code != 0
    assert "Import failed" in result.output


def test_cli_non_oauth_prompts_email(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    monkeypatch.setattr(cli_mod.click, "prompt", lambda *_a, **_kw: "you@example.com")
    monkeypatch.setattr(cli_mod, "login_keep", lambda *_a, **_kw: (object(), True))
    monkeypatch.setattr(cli_mod, "import_lines_from_path", lambda *_a, **_kw: (2, 0))
    result = runner.invoke(cli_mod.cli, [str(file)])
    assert result.exit_code == 0
    assert "Master token saved" in result.output
    assert "Imported 2 note(s)" in result.output


def test_cli_non_oauth_login_failure(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    monkeypatch.setattr(cli_mod.click, "prompt", lambda *_a, **_kw: "you@example.com")
    monkeypatch.setattr(cli_mod, "login_keep", lambda *_a, **_kw: (_ for _ in ()).throw(cli_mod.KeepUserError("bad creds")))
    result = runner.invoke(cli_mod.cli, [str(file)])
    assert result.exit_code != 0
    assert "bad creds" in result.output


def test_cli_oauth_reset_requires_email(tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    result = runner.invoke(cli_mod.cli, [str(file), "--oauth", "--reset-oauth"])
    assert result.exit_code != 0
    assert "requires --email" in result.output


def test_cli_oauth_auth_exceptions(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    file = write_sample(tmp_path)
    secrets = tmp_path / "client.json"
    secrets.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cli_mod,
        "oauth_credentials_cli",
        lambda *_a, **_kw: (_ for _ in ()).throw(cli_mod.KeepUserError("oauth bad")),
    )
    result = runner.invoke(cli_mod.cli, [str(file), "--oauth", "--client-secrets", str(secrets)])
    assert result.exit_code != 0
    assert "oauth bad" in result.output
