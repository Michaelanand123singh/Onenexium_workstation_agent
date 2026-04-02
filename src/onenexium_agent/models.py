from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ActivitySample:
    """One observation at a point in time (serialized to Nexium ingest API)."""

    process_name: str
    idle: bool
    in_project_roots: bool
    sampled_at: str = field(default_factory=utc_now_iso)
    window_title: str | None = None
    """Sent to API only when policy allows; use match_title for heuristics when this is None."""
    match_title: str | None = None
    """Foreground title for in-project detection; omitted from API payload."""
    metadata: dict[str, Any] | None = None

    def to_api_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "sampledAt": self.sampled_at,
            "processName": self.process_name,
            "idle": self.idle,
            "inProjectRoots": self.in_project_roots,
        }
        if self.window_title is not None:
            d["windowTitle"] = self.window_title
        if self.metadata:
            d["metadata"] = self.metadata
        return d
