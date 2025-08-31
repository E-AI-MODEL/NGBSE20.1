from __future__ import annotations

from typing import NotRequired, TypedDict

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SeedData(TypedDict):
    """Raw seed structure as found in configuration files."""

    url: str
    asset_id: NotRequired[str | None]
    tags: NotRequired[list[str]]


class RuleData(TypedDict):
    """Raw rule structure as found in configuration files."""

    id: str
    pattern: str
    weight: NotRequired[float]


class ConfigData(TypedDict):
    """Raw configuration structure combining seeds and rules."""

    seeds: list[SeedData]
    rules: list[RuleData]
    options: NotRequired[dict[str, str]]


class Seed(BaseModel):
    url: HttpUrl
    asset_id: str | None = None
    tags: list[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: list[str] | None) -> list[str]:
        return v or []

class Rule(BaseModel):
    id: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    weight: float = Field(1.0, ge=0)

class Config(BaseModel):
    seeds: list[Seed] = []
    rules: list[Rule] = []
    options: dict[str, str] = {}
