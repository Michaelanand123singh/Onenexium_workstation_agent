from __future__ import annotations

import logging
import platform
from typing import Any

import httpx

from onenexium_agent import __version__
from onenexium_agent.workstation.constants import WORKSTATION_INGEST_PATH

log = logging.getLogger(__name__)


class IngestClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def post_samples(self, samples: list[dict[str, Any]]) -> None:
        url = f"{self._base}{WORKSTATION_INGEST_PATH}"
        body = {
            "hostname": platform.node(),
            "agentVersion": __version__,
            "samples": samples,
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url, json=body, headers=headers)
        if r.status_code == 401:
            raise RuntimeError("Ingest rejected (401): check ONENEXIUM_INGEST_TOKEN")
        if not r.is_success:
            log.warning("ingest HTTP %s: %s", r.status_code, r.text[:500])
            r.raise_for_status()
