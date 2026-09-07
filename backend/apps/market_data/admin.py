from django.contrib import admin

from .models import (
    CompanyProfile,
    FinancialStatement,
    InsiderTransaction,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
    PeerGroup,
    Sector,
    SecurityAlias,
    Ticker,
)

for model in (
    CompanyProfile,
    FinancialStatement,
    InsiderTransaction,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
    PeerGroup,
    Sector,
    SecurityAlias,
    Ticker,
):
    admin.site.register(model)
