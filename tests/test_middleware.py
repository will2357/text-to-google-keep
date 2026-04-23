from __future__ import annotations

import json

from django.test import RequestFactory

from ttgk.middleware import InertiaJsonPostMiddleware


def test_inertia_json_post_populates_post() -> None:
    factory = RequestFactory()
    req = factory.post(
        "/import/",
        data=json.dumps({"email": "you@example.com", "use_oauth": True, "x": None, "nested": {"a": 1}}),
        content_type="application/json",
        HTTP_X_INERTIA="true",
    )

    def _ok(request):
        assert request.POST["email"] == "you@example.com"
        assert request.POST["use_oauth"] == "true"
        assert request.POST["x"] == ""
        assert "nested" not in request.POST
        return request

    mw = InertiaJsonPostMiddleware(_ok)
    mw(req)


def test_inertia_json_post_ignores_invalid_json() -> None:
    factory = RequestFactory()
    req = factory.post("/import/", data="{bad", content_type="application/json", HTTP_X_INERTIA="true")

    mw = InertiaJsonPostMiddleware(lambda request: request)
    out = mw(req)
    assert out is req
