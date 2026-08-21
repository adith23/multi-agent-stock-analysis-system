from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import DataCategory, SourceType


class NormalizedRecordData(BaseModel):
    """Source-neutral value object passed from adapters to persistence."""

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    category: DataCategory
    source_type: SourceType | str
    source_id: str = ""
    entity_identifier: str = ""
    source_timestamp: datetime | None = None
    payload: dict[str, Any]
    schema_version: str = "1.0"
    language: str = "en"
    canonical_key: str = ""


class QualityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(ge=0.0, le=1.0)
    is_acceptable: bool
    issues: tuple[str, ...] = ()
    flags: dict[str, bool] = Field(default_factory=dict)


class IngestionBatchResult(BaseModel):
    source: str
    category: str
    requested: int = 0
    accepted: int = 0
    duplicates: int = 0
    rejected: int = 0
    failed: int = 0
    record_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
