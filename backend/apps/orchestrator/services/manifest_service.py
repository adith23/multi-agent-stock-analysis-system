from __future__ import annotations

import json
from typing import Any

from django.conf import settings

from apps.core.utils.hashing import canonical_json, content_hash
from apps.market_data.models import Ticker
from apps.risk_compliance.repositories import RiskComplianceRepository


class RunManifestService:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def build(
        cls,
        *,
        run_id,
        ticker: Ticker,
        data_cutoff_at,
        config: dict[str, Any],
    ) -> tuple[dict[str, Any], str, str]:
        configuration_hash = content_hash(config)
        governance_repository = RiskComplianceRepository()
        risk_limits = governance_repository.active_limits()
        compliance_policies = governance_repository.active_policies()
        restricted = ticker.symbol in governance_repository.restricted_symbols()
        governance_snapshot = {
            "risk_limits": risk_limits,
            "compliance_policies": compliance_policies,
            "restricted_security": restricted,
        }
        manifest = {
            "schema_version": cls.SCHEMA_VERSION,
            "analysis_run_id": str(run_id),
            "security": {
                "ticker_id": str(ticker.id),
                "symbol": ticker.symbol,
                "exchange": ticker.exchange,
                "currency": ticker.currency,
            },
            "data_cutoff_at": data_cutoff_at,
            "configuration_hash": configuration_hash,
            "runtime": {
                "llm_provider": settings.LLM_PROVIDER,
                "llm_default_model": settings.LLM_DEFAULT_MODEL,
                "llm_fallback_model": settings.LLM_FALLBACK_MODEL,
                "engine_contract_version": "1.0.0",
                "rule_contract_version": "1.0.0",
            },
            "governance": governance_snapshot,
            "governance_hash": content_hash(governance_snapshot),
            "point_in_time_policy": {
                "available_at_lte_data_cutoff": True,
                "future_observations_permitted": False,
            },
        }
        # A manifest is both hashable and persistable. Canonicalization converts
        # datetimes, decimals, enums, and sets into deterministic JSON values
        # before the snapshot reaches a JSONField.
        serializable_manifest = json.loads(canonical_json(manifest))
        return (
            serializable_manifest,
            configuration_hash,
            content_hash(serializable_manifest),
        )
