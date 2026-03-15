"""Canonical JSON serialization."""

from __future__ import annotations

import dataclasses
import enum
import json
from datetime import datetime
from typing import Any


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        if isinstance(o, enum.Enum):
            return o.value
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, cls=_Encoder, sort_keys=True, separators=(",", ":"))
