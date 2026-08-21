from django.contrib import admin

from .models import (
    ConvictionScorePackage,
    RegimeState,
    RegimeTransitionAlert,
    SignalAgreementMatrix,
    TechnicalSignal,
)

for model in (
    ConvictionScorePackage,
    RegimeState,
    RegimeTransitionAlert,
    SignalAgreementMatrix,
    TechnicalSignal,
):
    admin.site.register(model)
