from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import httpx

from onenexium_agent import __version__
from onenexium_agent.client import IngestClient
from onenexium_agent.collectors import get_collector
from onenexium_agent.config import load_settings
from onenexium_agent.local_store import LocalQueue
from onenexium_agent.models import ActivitySample
from onenexium_agent.project_match import in_company_project, normalize_path_prefixes
from onenexium_agent.spawn import run_configure_blocking

if TYPE_CHECKING:
    from onenexium_agent.config import Settings

log = logging.getLogger(__name__)

FAILURES_BEFORE_SETUP = 3


def _apply_project_flag(sample: ActivitySample, settings: Settings) -> ActivitySample:
    exe_path: str | None = None
    if sample.metadata and isinstance(sample.metadata.get("exe_path"), str):
        exe_path = sample.metadata["exe_path"]
    title = sample.window_title or sample.match_title or ""
    prefixes = normalize_path_prefixes([str(p) for p in settings.project_root_prefixes])
    in_proj = in_company_project(
        exe_path=exe_path,
        window_title=title,
        path_prefixes=prefixes,
        title_markers=list(settings.project_title_markers),
    )
    return ActivitySample(
        process_name=sample.process_name,
        idle=sample.idle,
        in_project_roots=in_proj,
        sampled_at=sample.sampled_at,
        window_title=sample.window_title,
        match_title=sample.match_title,
        metadata=sample.metadata,
    )


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_forever() -> None:
    """Reload settings after setup wizard; reopen wizard after repeated upload failures."""
    while True:
        settings = load_settings()
        _configure_logging(settings.log_level)

        if not settings.ingest_token:
            log.warning("No ingest token — opening configuration page…")
            run_configure_blocking()
            settings = load_settings()
            if not settings.ingest_token:
                raise SystemExit(
                    "Still no ingest token. Run: onenexium-agent configure"
                )

        data_dir = settings.resolved_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        queue = LocalQueue(data_dir / "queue.sqlite")
        collector = get_collector()
        client = IngestClient(settings.api_base_url, settings.ingest_token)

        log.info(
            "onenexium-agent %s starting (sample=%ss upload=%ss)",
            __version__,
            settings.sample_interval_seconds,
            settings.upload_interval_seconds,
        )

        last_upload = 0.0
        failure_streak = 0
        inner_exit = False
        while not inner_exit:
            loop_start = time.monotonic()
            try:
                raw = collector.collect(
                    idle_threshold_seconds=float(settings.idle_threshold_seconds),
                    send_window_titles=settings.send_window_titles,
                )
                sample = _apply_project_flag(raw, settings)
                queue.enqueue(sample.to_api_dict())
            except Exception:
                log.exception("sample failed")

            now = time.monotonic()
            pending = queue.pending_count()
            should_upload = (
                now - last_upload >= settings.upload_interval_seconds or pending >= 400
            )
            if should_upload and pending > 0:
                batch = queue.fetch_batch(500)
                if batch:
                    ids = [r[0] for r in batch]
                    payloads = [r[1] for r in batch]
                    try:
                        client.post_samples(payloads)
                        queue.delete_ids(ids)
                        last_upload = now
                        failure_streak = 0
                        log.info("uploaded %s samples", len(payloads))
                    except (httpx.HTTPError, OSError, RuntimeError) as e:
                        failure_streak += 1
                        log.warning(
                            "upload failed (%s/%s): %s",
                            failure_streak,
                            FAILURES_BEFORE_SETUP,
                            e,
                        )
                        if failure_streak >= FAILURES_BEFORE_SETUP:
                            log.warning(
                                "Opening configuration page after repeated failures…"
                            )
                            run_configure_blocking()
                            inner_exit = True

            elapsed = time.monotonic() - loop_start
            sleep_for = max(0.0, settings.sample_interval_seconds - elapsed)
            time.sleep(sleep_for)


def run_once() -> None:
    """Single sample + attempt flush (for Task Scheduler smoke tests)."""
    settings = load_settings()
    _configure_logging(settings.log_level)
    if not settings.ingest_token:
        log.warning("No ingest token — opening configuration page…")
        run_configure_blocking()
        settings = load_settings()
    if not settings.ingest_token:
        raise SystemExit("No ingest token. Run: onenexium-agent configure")

    data_dir = settings.resolved_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    queue = LocalQueue(data_dir / "queue.sqlite")
    collector = get_collector()
    raw = collector.collect(
        idle_threshold_seconds=float(settings.idle_threshold_seconds),
        send_window_titles=settings.send_window_titles,
    )
    sample = _apply_project_flag(raw, settings)
    queue.enqueue(sample.to_api_dict())

    client = IngestClient(settings.api_base_url, settings.ingest_token)
    batch = queue.fetch_batch(500)
    if batch:
        ids = [r[0] for r in batch]
        payloads = [r[1] for r in batch]
        client.post_samples(payloads)
        queue.delete_ids(ids)
        log.info("uploaded %s samples", len(payloads))
