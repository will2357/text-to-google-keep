"""Middleware for Inertia + Django (pattern from Sython)."""

from __future__ import annotations

import json

from django.http import QueryDict
from django.utils.datastructures import MultiValueDict


class InertiaJsonPostMiddleware:
    """Populate request.POST from Inertia JSON bodies (non-multipart)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        content_type = (request.content_type or "").split(";")[0].strip().lower()
        if (
            request.method in ("POST", "PUT", "PATCH", "DELETE")
            and request.headers.get("X-Inertia")
            and content_type == "application/json"
            and request.body
        ):
            try:
                payload = json.loads(request.body)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                post = QueryDict(mutable=True)
                for key, value in payload.items():
                    if isinstance(value, (dict, list)):
                        continue
                    if value is None:
                        post.setlist(key, [""])
                    elif isinstance(value, bool):
                        post.setlist(key, ["true" if value else "false"])
                    else:
                        post.setlist(key, [str(value)])
                request._post = post
                request._files = MultiValueDict()
        return self.get_response(request)
