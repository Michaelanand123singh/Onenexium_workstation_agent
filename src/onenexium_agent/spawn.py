from __future__ import annotations

import subprocess
import sys


def configure_command() -> list[str]:
    """Argv to open the local setup wizard (works for python -m and PyInstaller exe)."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "configure"]
    return [sys.executable, "-m", "onenexium_agent", "configure"]


def run_configure_blocking() -> int:
    return subprocess.run(configure_command(), check=False).returncode
