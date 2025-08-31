from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl, field_validator

class Seed(BaseModel):
    url: HttpUrl
    asset_id: Optional[str] = None
    tags: List[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v):
        return v or []

class Rule(BaseModel):
    id: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    weight: float = Field(1.0, ge=0)

class Config(BaseModel):
    seeds: List[Seed] = []
    rules: List[Rule] = []
    options: Dict[str, str] = {}
