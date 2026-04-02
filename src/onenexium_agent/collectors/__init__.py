from __future__ import annotations

import sys
from typing import Protocol

from onenexium_agent.collectors.stub import StubCollector
from onenexium_agent.models import ActivitySample


class ActivityCollector(Protocol):
    def collect(
        self,
        *,
        idle_threshold_seconds: float,
        send_window_titles: bool,
    ) -> ActivitySample: ...


def get_collector() -> ActivityCollector:
    if sys.platform == "win32":
        from onenexium_agent.collectors.windows import WindowsCollector

        return WindowsCollector()
    return StubCollector()
