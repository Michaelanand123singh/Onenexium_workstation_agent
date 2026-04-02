from __future__ import annotations

import logging

from onenexium_agent.models import ActivitySample

log = logging.getLogger(__name__)


class StubCollector:
    """Non-Windows or CI: emits a placeholder sample."""

    def collect(
        self,
        *,
        idle_threshold_seconds: float,
        send_window_titles: bool,
    ) -> ActivitySample:
        void = idle_threshold_seconds
        void = send_window_titles
        log.debug("stub collector tick")
        return ActivitySample(
            process_name="stub",
            idle=False,
            in_project_roots=False,
            window_title=None,
            match_title="onenexium-stub",
            metadata={"collector": "stub"},
        )
