"""LLM boundary helpers shared by graph nodes."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from agents.base.contracts import AgentMetadata


def invoke_structured[SchemaT: BaseModel](
    llm: Any,
    schema: type[SchemaT],
    *,
    system_prompt: str,
    task: str,
    context: dict[str, Any],
) -> SchemaT:
    """Invoke an injected model and enforce the Pydantic output contract."""

    model = llm.with_structured_output(schema)
    result = model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"{task}\n\nVERIFIED INPUT CONTEXT:\n"
                f"{json.dumps(context, default=str, sort_keys=True)}"
            ),
        ]
    )
    return result if isinstance(result, schema) else schema.model_validate(result)


def attach_metadata(
    output: BaseModel,
    *,
    agent_id: str,
    agent_version: str,
    prompt_version: str,
    model_name: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Return a checkpoint-safe JSON representation with immutable provenance."""

    if model_name is None:
        from django.conf import settings

        model_name = str(getattr(settings, "LLM_DEFAULT_MODEL", "configured-llm"))
    data = output.model_dump(mode="json")
    data["metadata"] = AgentMetadata(
        agent_id=agent_id,
        agent_version=agent_version,
        prompt_version=prompt_version,
        model_name=model_name,
        warnings=warnings or [],
        degraded=bool(warnings),
    ).model_dump(mode="json")
    return data


def require_keys(data: dict[str, Any], *keys: str) -> None:
    missing = [key for key in keys if data.get(key) is None]
    if missing:
        raise ValueError(f"missing required agent inputs: {', '.join(missing)}")
