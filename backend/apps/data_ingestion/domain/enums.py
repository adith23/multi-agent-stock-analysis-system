from django.db import models


class SourceType(models.TextChoices):
    FINNHUB = "finnhub", "Finnhub"
    FRED = "fred", "Federal Reserve Economic Data"
    SEC_EDGAR = "sec_edgar", "SEC EDGAR"
    NEWS_API = "news_api", "NewsAPI"
    YFINANCE = "yfinance", "Yahoo Finance"
    ALPHA_VANTAGE = "alpha_vantage", "Alpha Vantage"


class DataCategory(models.TextChoices):
    QUOTE = "quote", "Quote"
    OHLCV = "ohlcv", "OHLCV"
    COMPANY_PROFILE = "company_profile", "Company profile"
    FINANCIAL_STATEMENT = "financial_statement", "Financial statement"
    FILING = "filing", "Regulatory filing"
    MACRO = "macro", "Macro indicator"
    NEWS = "news", "News"
    OWNERSHIP = "ownership", "Ownership"
    INSIDER_TRANSACTION = "insider_transaction", "Insider transaction"
    PEER_GROUP = "peer_group", "Peer group"
    ALTERNATIVE = "alternative", "Alternative data"


class IngestionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    ACCEPTED = "accepted", "Accepted"
    DUPLICATE = "duplicate", "Duplicate"
    REJECTED = "rejected", "Rejected"
    FAILED = "failed", "Failed"
