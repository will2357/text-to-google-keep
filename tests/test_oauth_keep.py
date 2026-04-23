from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from text_to_google_keep import oauth_keep


def test_resolve_client_secrets_path_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    explicit = tmp_path / "x.json"
    monkeypatch.setenv("GOOGLE_KEEP_CLIENT_SECRETS", str(tmp_path / "env.json"))
    assert oauth_keep.resolve_client_secrets_path(str(explicit)) == explicit.resolve()


def test_resolve_client_secrets_path_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_path = tmp_path / "env.json"
    monkeypatch.setenv("GOOGLE_KEEP_CLIENT_SECRETS", str(env_path))
    assert oauth_keep.resolve_client_secrets_path(None) == env_path.resolve()


def test_resolve_client_secrets_path_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GOOGLE_KEEP_CLIENT_SECRETS", raising=False)
    monkeypatch.chdir(tmp_path)
    assert oauth_keep.resolve_client_secrets_path(None) == (tmp_path / "client_secret.json").resolve()


def test_fetch_google_email_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"email": "You@Example.com"}).encode()

    class _Resp:
        def read(self) -> bytes:
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(oauth_keep.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
    creds = SimpleNamespace(token="tok")
    assert oauth_keep.fetch_google_email(creds) == "you@example.com"


def test_fetch_google_email_missing_email(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def read(self) -> bytes:
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(oauth_keep.urllib.request, "urlopen", lambda *_a, **_kw: _Resp())
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.fetch_google_email(SimpleNamespace(token="tok"))


def test_fetch_google_email_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        oauth_keep.urllib.request,
        "urlopen",
        lambda *_a, **_kw: (_ for _ in ()).throw(OSError("no net")),
    )
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.fetch_google_email(SimpleNamespace(token="tok"))


def test_clear_oauth_ignores_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        oauth_keep.keyring,
        "delete_password",
        lambda *_a, **_kw: (_ for _ in ()).throw(oauth_keep.keyring.errors.PasswordDeleteError()),
    )
    oauth_keep.clear_oauth("u@example.com")


def test_oauth_credentials_cli_missing_file(tmp_path: Path) -> None:
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.oauth_credentials_cli(tmp_path / "none.json", email=None, reset=False)


def test_oauth_credentials_cli_uses_saved_blob(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "client.json"
    path.write_text("{}", encoding="utf-8")
    creds = SimpleNamespace()
    monkeypatch.setattr(oauth_keep, "load_oauth_json", lambda _e: '{"refresh_token":"x"}')
    monkeypatch.setattr(oauth_keep, "_creds_from_json", lambda _blob: creds)
    monkeypatch.setattr(oauth_keep, "_refresh_and_persist", lambda _e, c: c)
    out, account = oauth_keep.oauth_credentials_cli(path, email="u@example.com", reset=False)
    assert out is creds
    assert account == "u@example.com"


def test_oauth_credentials_cli_interactive_saves(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "client.json"
    path.write_text("{}", encoding="utf-8")
    creds = SimpleNamespace(to_json=lambda: '{"ok":1}')
    flow = SimpleNamespace(run_local_server=lambda **_k: creds)
    saved: list[tuple[str, str]] = []
    monkeypatch.setattr(oauth_keep, "InstalledAppFlow", SimpleNamespace(from_client_secrets_file=lambda *_a, **_kw: flow))
    monkeypatch.setattr(oauth_keep, "fetch_google_email", lambda _c: "you@example.com")
    monkeypatch.setattr(oauth_keep, "save_oauth_json", lambda e, b: saved.append((e, b)))
    out, account = oauth_keep.oauth_credentials_cli(path, email=None, reset=False)
    assert out is creds
    assert account == "you@example.com"
    assert saved == [("you@example.com", '{"ok":1}')]


def test_oauth_credentials_cli_mismatch_email(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "client.json"
    path.write_text("{}", encoding="utf-8")
    creds = SimpleNamespace(to_json=lambda: "{}")
    flow = SimpleNamespace(run_local_server=lambda **_k: creds)
    monkeypatch.setattr(oauth_keep, "InstalledAppFlow", SimpleNamespace(from_client_secrets_file=lambda *_a, **_kw: flow))
    monkeypatch.setattr(oauth_keep, "fetch_google_email", lambda _c: "actual@example.com")
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.oauth_credentials_cli(path, email="expected@example.com", reset=False)


def test_import_lines_rest_counts_and_truncates() -> None:
    created: list[dict] = []

    class _Notes:
        def create(self, body):
            created.append(body)
            return SimpleNamespace(execute=lambda: None)

    service = SimpleNamespace(notes=lambda: _Notes())
    long_line = "x" * 21000
    count, skipped = oauth_keep.import_lines_rest(service, [long_line + "\n", "\n"], blank=False)
    assert (count, skipped) == (1, 1)
    assert len(created[0]["body"]["text"]["text"]) == 20000


def test_import_lines_rest_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHttpError(Exception):
        def __init__(self) -> None:
            self.resp = SimpleNamespace(status=403)
            self.content = b'{"error":"denied"}'

    monkeypatch.setattr(oauth_keep, "HttpError", FakeHttpError)

    class _Notes:
        def create(self, body):  # noqa: ARG002
            return SimpleNamespace(execute=lambda: (_ for _ in ()).throw(FakeHttpError()))

    service = SimpleNamespace(notes=lambda: _Notes())
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.import_lines_rest(service, ["x\n"], blank=False)


def test_oauth_credentials_web_saved_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oauth_keep, "load_oauth_json", lambda _e: None)
    with pytest.raises(oauth_keep.KeepUserError):
        oauth_keep.oauth_credentials_web_saved("u@example.com", reset=False)


def test_oauth_credentials_web_saved_refreshes(monkeypatch: pytest.MonkeyPatch) -> None:
    creds = SimpleNamespace()
    monkeypatch.setattr(oauth_keep, "load_oauth_json", lambda _e: '{"token":"x"}')
    monkeypatch.setattr(oauth_keep, "_creds_from_json", lambda _b: creds)
    monkeypatch.setattr(oauth_keep, "_refresh_and_persist", lambda _e, c: c)
    assert oauth_keep.oauth_credentials_web_saved("u@example.com", reset=True) is creds


def test_oauth_helpers() -> None:
    assert oauth_keep.oauth_keyring_account(" You@Example.com ") == "you@example.com"
    flow = SimpleNamespace(
        authorization_url=lambda **_kw: ("https://auth.example", "state"),
    )
    assert oauth_keep.oauth_authorization_url(flow) == ("https://auth.example", "state")


def test_refresh_and_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    class Creds:
        expired = True
        refresh_token = "r"

        def refresh(self, _req) -> None:
            calls.append(("refresh", "ok"))

        def to_json(self) -> str:
            return '{"new":1}'

    monkeypatch.setattr(oauth_keep, "save_oauth_json", lambda e, b: calls.append((e, b)))
    creds = Creds()
    out = oauth_keep._refresh_and_persist("you@example.com", creds)  # noqa: SLF001
    assert out is creds
    assert calls[0] == ("refresh", "ok")
    assert calls[1] == ("you@example.com", '{"new":1}')
