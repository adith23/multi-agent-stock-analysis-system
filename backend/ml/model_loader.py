"""Resolve ML model artifacts from local storage or a private GCS bucket."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from django.conf import settings

logger = logging.getLogger(__name__)


class ModelArtifactError(RuntimeError):
    """Raised when a configured model artifact cannot be resolved safely."""


def get_model_path(model_name: str) -> Path:
    """Return a local model path, downloading its GCS prefix atomically if needed."""
    safe_name = _safe_model_name(model_name)
    configured_path = Path(settings.ML_MODEL_DIR) / safe_name
    if _has_model_artifact(configured_path):
        return configured_path
    if not settings.GCS_ML_MODELS_BUCKET:
        raise FileNotFoundError(f"Model artifact not found: {configured_path}")

    cache_root = Path(settings.ML_MODEL_CACHE_DIR)
    cached_path = cache_root / safe_name
    if _has_model_artifact(cached_path):
        return cached_path
    return _download_from_gcs(safe_name, cached_path)


def _download_from_gcs(model_name: str, destination: Path) -> Path:
    from google.cloud import storage

    cache_root = destination.parent
    cache_root.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix="model-", dir=cache_root))
    temporary_destination = temporary_root / model_name
    try:
        bucket = storage.Client().bucket(settings.GCS_ML_MODELS_BUCKET)
        prefix = f"{model_name.rstrip('/')}/"
        blobs = list(bucket.list_blobs(prefix=prefix))
        if not blobs:
            # A model may be represented by one object instead of a directory.
            blob = bucket.get_blob(model_name)
            blobs = [blob] if blob is not None else []
        if not blobs:
            raise ModelArtifactError(f"No GCS objects found for model: {model_name}")

        for blob in blobs:
            relative = _relative_blob_path(blob.name, model_name)
            target = temporary_destination / relative if relative else temporary_destination
            target.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(target))
            logger.info("ml.model_downloaded", extra={"blob": blob.name, "path": str(target)})

        if destination.exists():
            return destination
        temporary_destination.replace(destination)
        return destination
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)


def _safe_model_name(model_name: str) -> str:
    path = PurePosixPath(model_name)
    if not model_name or path.is_absolute() or ".." in path.parts or "\\" in model_name:
        raise ModelArtifactError("model_name must be a safe relative GCS prefix")
    return path.as_posix().strip("/")


def _has_model_artifact(path: Path) -> bool:
    if path.is_file():
        return True
    if not path.is_dir():
        return False
    placeholders = {".gitkeep", "readme.md"}
    return any(
        child.is_file() and child.name.casefold() not in placeholders for child in path.rglob("*")
    )


def _relative_blob_path(blob_name: str, model_name: str) -> Path | None:
    if blob_name == model_name:
        return None
    prefix = f"{model_name.rstrip('/')}/"
    if not blob_name.startswith(prefix):
        raise ModelArtifactError(f"Unexpected object outside model prefix: {blob_name}")
    relative = PurePosixPath(blob_name.removeprefix(prefix))
    if not relative.parts:
        return None
    if relative.is_absolute() or ".." in relative.parts:
        raise ModelArtifactError(f"Unsafe model object path: {blob_name}")
    return Path(*relative.parts)
