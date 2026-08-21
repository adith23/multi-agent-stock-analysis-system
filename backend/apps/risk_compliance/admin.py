from django.contrib import admin

from .models import (
    ComplianceResult,
    ComplianceRule,
    PortfolioState,
    RestrictedSecurity,
    RiskLimit,
    RiskValidationResult,
)

admin.site.register(
    (
        ComplianceResult,
        ComplianceRule,
        PortfolioState,
        RestrictedSecurity,
        RiskLimit,
        RiskValidationResult,
    )
)
