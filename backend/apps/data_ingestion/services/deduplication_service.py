from __future__ import annotations

from apps.core.utils.hashing import content_hash, hamming_distance, simhash
from apps.data_ingestion.domain import DataCategory
from apps.data_ingestion.models import NormalizedDataRecord


class DeduplicationService:
    """Exact SHA-256 and bounded SimHash near-duplicate detection."""

    def __init__(self, *, max_hamming_distance: int = 3, candidate_limit: int = 250) -> None:
        self.max_hamming_distance = max_hamming_distance
        self.candidate_limit = candidate_limit

    @staticmethod
    def exact_fingerprint(payload: object) -> str:
        return content_hash(payload)

    @staticmethod
    def similarity_fingerprint(text: str) -> str:
        return f"{simhash(text):016x}"

    def exact_exists(self, *, source_type: str, category: str, fingerprint: str) -> bool:
        return NormalizedDataRecord.objects.filter(
            source_type=source_type,
            data_category=category,
            content_hash=fingerprint,
        ).exists()

    def find_near_duplicate(self, *, category: str, text: str) -> NormalizedDataRecord | None:
        if category not in {DataCategory.NEWS, DataCategory.FILING} or not text.strip():
            return None
        fingerprint = simhash(text)
        candidates = NormalizedDataRecord.objects.filter(
            data_category=category,
            similarity_hash__gt="",
        ).order_by("-created_at")[: self.candidate_limit]
        for candidate in candidates:
            if hamming_distance(fingerprint, int(candidate.similarity_hash, 16)) <= (
                self.max_hamming_distance
            ):
                return candidate
        return None

    @staticmethod
    def searchable_text(category: str, payload: dict) -> str:
        if category == DataCategory.NEWS:
            return " ".join(str(payload.get(key, "")) for key in ("headline", "summary", "body"))
        if category == DataCategory.FILING:
            return str(payload.get("content", ""))
        return ""
