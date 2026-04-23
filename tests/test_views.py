from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test.client import RequestFactory

from text_to_google_keep.core import KeepUserError


def messages_from(response) -> list[str]:
    return [str(m) for m in get_messages(response.wsgi_request)]


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture(autouse=True)
def _cookie_sessions(settings) -> None:
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


def test_home_renders(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_import_create_requires_email(client: Client) -> None:
    response = client.post("/import/", {"content": "x"})
    assert response.status_code == 302
    assert any("Email is required" in m for m in messages_from(response))


def test_import_create_requires_content(client: Client) -> None:
    response = client.post("/import/", {"email": "you@example.com", "content": "   "})
    assert response.status_code == 302
    assert any("Paste text or choose" in m for m in messages_from(response))


def test_import_create_oauth_rejects_labels(client: Client) -> None:
    response = client.post(
        "/import/",
        {"email": "you@example.com", "content": "x", "use_oauth": "true", "labels": "A"},
    )
    assert response.status_code == 302
    assert any("not supported" in m for m in messages_from(response))


def test_import_create_oauth_success(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    created: list[dict] = []
    monkeypatch.setattr(views, "oauth_credentials_web_saved", lambda *_a, **_kw: object())
    monkeypatch.setattr(views, "build_keep_service", lambda _c: object())
    monkeypatch.setattr(views, "import_lines_rest", lambda *_a, **_kw: (2, 1))
    monkeypatch.setattr(views.ImportLog.objects, "create", lambda **kw: created.append(kw))
    response = client.post(
        "/import/",
        {"email": "you@example.com", "content": "a\n\n", "use_oauth": "true", "blank_lines": "false"},
    )
    assert response.status_code == 302
    assert any("Imported 2 note(s) via Google OAuth" in m for m in messages_from(response))
    assert created and created[0]["auth_method"] == views.ImportLog.AuthMethod.OAUTH


def test_import_create_oauth_failure(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    monkeypatch.setattr(
        views,
        "oauth_credentials_web_saved",
        lambda *_a, **_kw: (_ for _ in ()).throw(KeepUserError("oauth missing")),
    )
    response = client.post(
        "/import/",
        {"email": "you@example.com", "content": "x", "use_oauth": "true"},
    )
    assert response.status_code == 302
    assert any("oauth missing" in m for m in messages_from(response))


def test_import_create_gkeep_success(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    created: list[dict] = []
    monkeypatch.setattr(views, "login_keep", lambda *_a, **_kw: (object(), True))
    monkeypatch.setattr(views, "import_lines", lambda *_a, **_kw: (1, 0))
    monkeypatch.setattr(views.ImportLog.objects, "create", lambda **kw: created.append(kw))
    response = client.post("/import/", {"email": "you@example.com", "content": "x"})
    assert response.status_code == 302
    msg = " ".join(messages_from(response))
    assert "Imported 1 note(s)." in msg
    assert "Master token saved" in msg
    assert created and created[0]["auth_method"] == views.ImportLog.AuthMethod.GKEEPAPI


def test_import_create_user_error(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    monkeypatch.setattr(
        views,
        "login_keep",
        lambda *_a, **_kw: (_ for _ in ()).throw(KeepUserError("bad creds")),
    )
    response = client.post("/import/", {"email": "you@example.com", "content": "x"})
    assert response.status_code == 302
    assert any("bad creds" in m for m in messages_from(response))


def test_oauth_start_missing_secrets(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    monkeypatch.setattr(views, "resolve_client_secrets_path", lambda _x: SimpleNamespace(is_file=lambda: False))
    response = client.get("/oauth/start/")
    assert response.status_code == 302
    assert any("client secrets not found" in m for m in messages_from(response))


def test_oauth_start_success_sets_session(monkeypatch: pytest.MonkeyPatch, client: Client) -> None:
    from pages import views

    class FakeFlow:
        code_verifier = "verifier"

    monkeypatch.setattr(views, "resolve_client_secrets_path", lambda _x: SimpleNamespace(is_file=lambda: True, __str__=lambda s: "/tmp/client.json"))
    monkeypatch.setattr(views, "oauth_flow_for_redirect", lambda *_a, **_kw: FakeFlow())
    monkeypatch.setattr(views, "oauth_authorization_url", lambda _f: ("https://example.com/auth", "state1"))
    response = client.get("/oauth/start/")
    assert response.status_code == 302
    assert response["Location"] == "https://example.com/auth"
    sess = client.session
    assert sess["oauth_state"] == "state1"
    assert sess["oauth_code_verifier"] == "verifier"


def test_oauth_callback_state_mismatch(client: Client) -> None:
    from pages import views

    req = RequestFactory().get("/oauth/callback/?state=wrong")
    SessionMiddleware(lambda _r: None).process_request(req)
    req.session["oauth_state"] = "expected"
    req.session["oauth_redirect_uri"] = "http://127.0.0.1:8001/oauth/callback/"
    req.session["oauth_secrets_path"] = "/tmp/client.json"
    req.session.save()
    setattr(req, "_messages", FallbackStorage(req))
    response = views.oauth_callback(req)
    assert response.status_code == 302


def test_oauth_callback_error_query(client: Client) -> None:
    response = client.get("/oauth/callback/?error=access_denied&error_description=nope", follow=True)
    assert response.status_code == 200
    assert "nope" in response.content.decode()


def test_oauth_callback_missing_session(client: Client) -> None:
    response = client.get("/oauth/callback/?state=ok", follow=True)
    assert response.status_code == 200
    assert "session expired" in response.content.decode()


def test_oauth_callback_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from pages import views

    class FakeFlow:
        credentials = SimpleNamespace(to_json=lambda: '{"ok":1}')

        def fetch_token(self, authorization_response: str) -> None:
            assert "state=ok" in authorization_response

    monkeypatch.setattr(views, "Flow", SimpleNamespace(from_client_secrets_file=lambda *_a, **_kw: FakeFlow()))
    monkeypatch.setattr(views, "fetch_google_email", lambda _c: "you@example.com")
    saved: list[tuple[str, str]] = []
    monkeypatch.setattr(views, "save_oauth_json", lambda e, b: saved.append((e, b)))
    req = RequestFactory().get("/oauth/callback/?state=ok")
    SessionMiddleware(lambda _r: None).process_request(req)
    req.session["oauth_state"] = "ok"
    req.session["oauth_code_verifier"] = "verifier"
    req.session["oauth_redirect_uri"] = "http://127.0.0.1:8001/oauth/callback/"
    req.session["oauth_secrets_path"] = "/tmp/client.json"
    req.session.save()
    setattr(req, "_messages", FallbackStorage(req))
    response = views.oauth_callback(req)
    assert response.status_code == 302
    assert saved == [("you@example.com", '{"ok":1}')]
    assert "oauth_state" not in req.session


def test_oauth_callback_failure_clears_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from pages import views

    monkeypatch.setattr(
        views,
        "Flow",
        SimpleNamespace(from_client_secrets_file=lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("boom"))),
    )
    req = RequestFactory().get("/oauth/callback/?state=ok")
    SessionMiddleware(lambda _r: None).process_request(req)
    req.session["oauth_state"] = "ok"
    req.session["oauth_code_verifier"] = "verifier"
    req.session["oauth_redirect_uri"] = "http://127.0.0.1:8001/oauth/callback/"
    req.session["oauth_secrets_path"] = "/tmp/client.json"
    req.session.save()
    setattr(req, "_messages", FallbackStorage(req))
    response = views.oauth_callback(req)
    assert response.status_code == 302
    assert "oauth_state" not in req.session
