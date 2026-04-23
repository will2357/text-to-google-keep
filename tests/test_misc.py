from __future__ import annotations

from datetime import datetime, timezone

from pages.models import ImportLog
from text_to_google_keep import __version__


def test_version_present() -> None:
    assert __version__


def test_import_log_str() -> None:
    log = ImportLog(
        email="you@example.com",
        auth_method=ImportLog.AuthMethod.OAUTH,
        lines_imported=1,
        lines_skipped=0,
    )
    log.created_at = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    assert "you@example.com" in str(log)
    assert "(oauth)" in str(log)
