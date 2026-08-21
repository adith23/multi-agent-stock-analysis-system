from django.contrib import admin

from apps.audit.models import AuditTrailRecord


@admin.register(AuditTrailRecord)
class AuditTrailRecordAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "event_type",
        "action",
        "actor_label",
        "resource_type",
        "status_code",
    )
    list_filter = ("event_type", "action", "status_code")
    search_fields = ("request_id", "actor_label", "resource_type", "resource_id", "summary")
    readonly_fields = [field.name for field in AuditTrailRecord._meta.fields]
    date_hierarchy = "occurred_at"

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser and obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
