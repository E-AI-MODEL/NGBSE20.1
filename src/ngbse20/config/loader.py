from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple
from pydantic import ValidationError

from .models import Config, Seed, Rule

def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_seeds(path: str) -> List[Seed]:
    p = Path(path)
    items: list[Seed] = []
    if p.suffix.lower() == ".jsonl":
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                items.append(Seed.model_validate_json(line))
            except ValidationError as e:
                raise ValueError(f"Seed op regel {ln} faalt validatie: {e}") from e
    else:
        data = _read_json(p)
        try:
            items = [Seed(**s) for s in data]
        except ValidationError as e:
            raise ValueError(f"Seeds faalden validatie: {e}") from e
    return items

def load_rules(path: str) -> List[Rule]:
    p = Path(path)
    data = _read_json(p)
    try:
        return [Rule(**r) for r in data]
    except ValidationError as e:
        raise ValueError(f"Rules faalden validatie: {e}") from e

def load_config(seeds_path: str, rules_path: str) -> Config:
    seeds = load_seeds(seeds_path)
    rules = load_rules(rules_path)
    return Config(seeds=seeds, rules=rules)

def validate_files(seeds_path: str, rules_path: str) -> Tuple[int, int]:
    """Geeft (#seeds, #rules) terug of raise't ValueError met duidelijke boodschap."""
    cfg = load_config(seeds_path, rules_path)
    return (len(cfg.seeds), len(cfg.rules))
