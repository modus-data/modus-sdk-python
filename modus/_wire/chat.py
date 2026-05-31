"""Wire models for skill/agent chat — matches OpenAPI SkillChat* DTOs."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _SkillChatRequestWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    message: str
    model: str


class _SkillChatResponseWire(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    content: str
    thread_id: str = Field(alias="threadId")
    run_id: str = Field(alias="runId")
