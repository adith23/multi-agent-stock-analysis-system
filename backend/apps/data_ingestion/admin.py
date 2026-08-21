from django.contrib import admin

from .models import DataSourceConfiguration, NormalizedDataRecord, RawInputObject


@admin.register(DataSourceConfiguration)
class DataSourceConfigurationAdmin(admin.ModelAdmin):
    list_display = ("display_name", "source_type", "is_enabled", "priority", "last_success_at")
    list_filter = ("is_enabled", "source_type")


@admin.register(RawInputObject)
class RawInputObjectAdmin(admin.ModelAdmin):
    list_display = ("source_type", "data_category", "entity_identifier", "status", "fetched_at")
    list_filter = ("source_type", "data_category", "status")
    readonly_fields = ("raw_payload", "raw_text", "content_hash", "fetched_at")


@admin.register(NormalizedDataRecord)
class NormalizedDataRecordAdmin(admin.ModelAdmin):
    list_display = (
        "source_type",
        "data_category",
        "entity_identifier",
        "data_quality_score",
        "status",
    )
    list_filter = ("source_type", "data_category", "status")
