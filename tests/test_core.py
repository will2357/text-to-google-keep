from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import gkeepapi.exception as gexc
import keyring
import pytest

from text_to_google_keep import core


class FakeNote:
    def __init__(self) -> None:
        self.labels = set()


class FakeKeep:
    def __init__(self) -> None:
        self.labels: dict[str, str] = {}
        self.created_notes: list[tuple[None, str]] = []
        self.synced = False
        self.authenticate_calls: list[tuple[str, str]] = []
        self.login_calls: list[tuple[str, str]] = []
        self.master_token = "mtok"

    def createLabel(self, name: str) -> None:  # noqa: N802
        if name in self.labels:
            raise gexc.LabelException("Label exists")
        self.labels[name] = name

    def findLabel(self, name: str):  # noqa: N802
        return self.labels.get(name)

    def createNote(self, _title, text: str):  # noqa: N802
        note = FakeNote()
        self.created_notes.append((_title, text))
        return note

    def sync(self) -> None:
        self.synced = True

    def authenticate(self, email: str, token: str) -> None:
        self.authenticate_calls.append((email, token))

    def login(self, email: str, password: str) -> None:
        self.login_calls.append((email, password))

    def getMasterToken(self) -> str:  # noqa: N802
        return self.master_token


def test_parse_labels_csv() -> None:
    assert core.parse_labels_csv("A, B\nC,,") == ["A", "B", "C"]


def test_clear_token_ignores_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_svc: str, _acc: str) -> None:
        raise keyring.errors.PasswordDeleteError()

    monkeypatch.setattr(core.keyring, "delete_password", _raise)
    core.clear_token("A@B.com")


def test_attach_label_creates_and_attaches() -> None:
    keep = FakeKeep()
    note = FakeNote()
    core.attach_label(keep, note, "Work")
    assert "Work" in note.labels


def test_attach_label_raises_when_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    note = FakeNote()
    monkeypatch.setattr(keep, "findLabel", lambda _name: None)
    with pytest.raises(core.KeepUserError):
        core.attach_label(keep, note, "Nope")


def test_login_keep_uses_token_and_skips_save(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: "saved-token")
    got, saved = core.login_keep("user@example.com")
    assert got is keep
    assert saved is False
    assert keep.authenticate_calls == [("user@example.com", "saved-token")]


def test_login_keep_token_failure_is_user_error(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()

    def _boom(_email: str, _token: str) -> None:
        raise gexc.LoginException("bad")

    keep.authenticate = _boom  # type: ignore[method-assign]
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: "saved-token")
    with pytest.raises(core.KeepUserError):
        core.login_keep("user@example.com")


def test_login_keep_requires_password_or_token(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: None)
    with pytest.raises(core.KeepUserError):
        core.login_keep("user@example.com")


def test_login_keep_password_path_saves_token(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    saved_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: None)
    monkeypatch.setattr(core, "save_token", lambda email, token: saved_calls.append((email, token)))
    got, saved = core.login_keep("user@example.com", password="pw")
    assert got is keep
    assert saved is True
    assert keep.login_calls == [("user@example.com", "pw")]
    assert saved_calls == [("user@example.com", "mtok")]


def test_login_keep_explicit_master_token_not_saved(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "save_token", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("should not save")))
    got, saved = core.login_keep("user@example.com", master_token="explicit")
    assert got is keep
    assert saved is False


def test_login_keep_browser_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()

    def _raise(_email: str, _password: str) -> None:
        exc = gexc.BrowserLoginRequiredException("verify")
        exc.url = "https://verify.example"
        raise exc

    keep.login = _raise  # type: ignore[method-assign]
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: None)
    with pytest.raises(core.KeepUserError) as err:
        core.login_keep("user@example.com", password="pw")
    assert "browser verification" in str(err.value).lower()


def test_login_keep_password_login_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    keep.login = lambda *_a, **_kw: (_ for _ in ()).throw(gexc.LoginException("bad"))  # type: ignore[method-assign]
    monkeypatch.setattr(core.gkeepapi, "Keep", lambda: keep)
    monkeypatch.setattr(core, "load_token", lambda _email: None)
    with pytest.raises(core.KeepUserError):
        core.login_keep("user@example.com", password="pw")


def test_import_lines_handles_blank_and_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    keep = FakeKeep()
    attached: list[str] = []
    monkeypatch.setattr(core, "attach_label", lambda _k, _n, name: attached.append(name))
    count, skipped = core.import_lines(keep, ["one\n", "\n", "two\r\n"], ["A", "B"], blank=False)
    assert (count, skipped) == (2, 1)
    assert attached == ["A", "B", "A", "B"]
    assert keep.synced is True


def test_import_lines_from_path(tmp_path: Path) -> None:
    file = tmp_path / "notes.txt"
    file.write_text("one\ntwo\n", encoding="utf-8")
    keep = FakeKeep()
    count, skipped = core.import_lines_from_path(keep, file, [], blank=False)
    assert (count, skipped) == (2, 0)


def test_import_lines_blank_true_imports_empty() -> None:
    keep = FakeKeep()
    count, skipped = core.import_lines(keep, ["\n"], [], blank=True)
    assert (count, skipped) == (1, 0)
