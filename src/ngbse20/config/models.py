from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Seed(BaseModel):
    url: HttpUrl
    asset_id: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

class Rule(BaseModel):
    id: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    weight: float = Field(1.0, ge=0)

class Config(BaseModel):
    seeds: list[Seed] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)
    options: dict[str, str] = Field(default_factory=dict)
