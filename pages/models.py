from django.db import models


class ImportLog(models.Model):
    """Audit trail for imports (PostgreSQL-backed)."""

    class AuthMethod(models.TextChoices):
        GKEEPAPI = "gkeepapi", "gkeepapi"
        OAUTH = "oauth", "oauth"

    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    auth_method = models.CharField(max_length=16, choices=AuthMethod.choices)
    lines_imported = models.PositiveIntegerField()
    lines_skipped = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} @ {self.created_at:%Y-%m-%d %H:%M} ({self.auth_method})"
