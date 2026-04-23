from django.contrib import admin

from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "email", "auth_method", "lines_imported", "lines_skipped")
    list_filter = ("auth_method",)
    readonly_fields = ("created_at", "email", "auth_method", "lines_imported", "lines_skipped")
