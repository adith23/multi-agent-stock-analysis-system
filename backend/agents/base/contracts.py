"""Shared, versioned contracts for all agent inputs and outputs."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentStance(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class EvidenceItem(BaseModel):
    """A traceable claim-to-source link, never an unstructured citation string."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    as_of: datetime | None = None
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)


class AgentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    agent_version: str
    prompt_version: str
    schema_version: str = "1.0.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_name: str = "configured-llm"
    degraded: bool = False
    warnings: list[str] = Field(default_factory=list)


class AgentInputBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_run_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1, max_length=32)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


class AgentOutputBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: AgentMetadata | None = None
