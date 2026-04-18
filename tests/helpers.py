"""
Comparison helpers for parity tests.

Because local and cloud ShotGrid have different entity IDs, we normalize
results before comparison so that ``assert normalize(local) == normalize(cloud)``
works for most cases.
"""
from __future__ import annotations

import copy
from typing import Any


def _strip_ids(obj: Any) -> Any:
    """Recursively strip ``id`` from dicts and entity references."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "id":
                continue
            out[k] = _strip_ids(v)
        return out
    if isinstance(obj, list):
        return [_strip_ids(i) for i in obj]
    return obj


def normalize(entity: dict | None, fields: list[str] | None = None) -> dict | None:
    """Return a copy of *entity* suitable for cross-server comparison.

    - Removes ``id`` at every level (top-level and nested entity refs).
    - If *fields* is given, only those keys (plus ``type``) are kept.
    """
    if entity is None:
        return None
    e = copy.deepcopy(entity)
    e = _strip_ids(e)
    if fields:
        keep = set(fields) | {"type"}
        e = {k: v for k, v in e.items() if k in keep}
    return e


def normalize_list(entities: list[dict], sort_key: str = "code",
                   fields: list[str] | None = None) -> list[dict]:
    """Normalize a list of entities and sort by *sort_key* for stable comparison."""
    normed = [normalize(e, fields) for e in entities]
    return sorted(normed, key=lambda x: x.get(sort_key, ""))


def assert_same_entity(local: dict | None, cloud: dict | None,
                       fields: list[str] | None = None, msg: str = ""):
    """Assert two entities are equivalent after normalization."""
    nl = normalize(local, fields)
    nc = normalize(cloud, fields)
    assert nl == nc, f"{msg}\nlocal:  {nl}\ncloud:  {nc}"


def assert_same_list(local_list: list[dict], cloud_list: list[dict],
                     sort_key: str = "code",
                     fields: list[str] | None = None, msg: str = ""):
    """Assert two entity lists are equivalent after normalization + sort."""
    nl = normalize_list(local_list, sort_key, fields)
    nc = normalize_list(cloud_list, sort_key, fields)
    assert nl == nc, f"{msg}\nlocal:  {nl}\ncloud:  {nc}"
