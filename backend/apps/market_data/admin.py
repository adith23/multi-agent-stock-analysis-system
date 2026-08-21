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
    Ticker,
):
    admin.site.register(model)
