from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

import psutil

from onenexium_agent.models import ActivitySample

log = logging.getLogger(__name__)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def _idle_seconds() -> float:
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    tick = kernel32.GetTickCount()
    elapsed_ms = (tick - lii.dwTime) & 0xFFFFFFFF
    return float(elapsed_ms) / 1000.0


def _foreground_pid() -> int | None:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value) if pid.value else None


def _window_title(hwnd: wintypes.HWND) -> str:
    length = user32.GetWindowTextLengthW(hwnd) + 1
    if length <= 1:
        return ""
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return buf.value or ""


class WindowsCollector:
    def collect(
        self,
        *,
        idle_threshold_seconds: float,
        send_window_titles: bool,
    ) -> ActivitySample:
        idle_sec = _idle_seconds()
        idle = idle_sec >= idle_threshold_seconds

        hwnd = user32.GetForegroundWindow()
        title = _window_title(hwnd) if hwnd else ""

        pid = _foreground_pid()
        process_name = "unknown"
        exe_path: str | None = None
        if pid is not None:
            try:
                proc = psutil.Process(pid)
                process_name = proc.name() or "unknown"
                exe_path = proc.exe()
            except (psutil.Error, OSError) as e:
                log.debug("process info failed: %s", e)

        return ActivitySample(
            process_name=process_name,
            idle=idle,
            in_project_roots=False,
            window_title=title if send_window_titles else None,
            match_title=title or None,
            metadata={"exe_path": exe_path, "idle_seconds": round(idle_sec, 1)},
        )
