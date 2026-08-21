from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.research.models import CatalystRecord


class CatalystMonitorService:
    @transaction.atomic
    def monitor(self) -> dict[str, int]:
        now = timezone.now()
        checked = delayed = 0
        catalysts = CatalystRecord.objects.filter(is_active=True, outcome_status="pending")
        for catalyst in catalysts.select_for_update():
            checked += 1
            catalyst.last_checked_at = now
            fields = ["last_checked_at", "updated_at"]
            if catalyst.expected_at and catalyst.expected_at < now:
                delayed += 1
                catalyst.outcome_status = "delayed"
                fields.append("outcome_status")
                if catalyst.is_thesis_critical and not catalyst.alert_sent:
                    catalyst.alert_sent = True
                    fields.append("alert_sent")
                    AuditService.record_event(
                        action=AuditAction.UPDATE,
                        event_type="research.catalyst_delayed",
                        resource_type="CatalystRecord",
                        resource_id=str(catalyst.id),
                        summary=f"Thesis-critical catalyst delayed: {catalyst.title}",
                    )
            catalyst.save(update_fields=fields)
        return {"checked": checked, "delayed": delayed}
