from django.contrib import admin

from .models import (
    BullBearDecisionMemo,
    CatalystRecord,
    EarningsQualityReport,
    PeerAnalysisReport,
    SpecialistReport,
    ValuationOutput,
)

for model in (
    BullBearDecisionMemo,
    CatalystRecord,
    EarningsQualityReport,
    PeerAnalysisReport,
    SpecialistReport,
    ValuationOutput,
):
    admin.site.register(model)
