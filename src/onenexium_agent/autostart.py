"""
Windows auto-start registration via the per-user registry Run key.

HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run

This is the same mechanism used by Slack, Discord, Steam, etc.
It requires no admin rights and survives reboots, sleep/wake, and fast-startup.
The entry is visible in Task Manager > Startup so the user is never surprised.

On non-Windows platforms the functions are safe no-ops.
"""

from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)

_REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "OnenexiumAgent"


def _get_exe_path() -> str:
    """Return the path to the running exe (frozen PyInstaller) or the Python script."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def _is_windows() -> bool:
    return sys.platform == "win32"


def ensure_autostart() -> bool:
    """
    Register (or update) the current exe in HKCU Run so it starts at logon.

    Called on every successful engine start so that:
    - First run: creates the entry
    - Exe moved to a new folder: updates the path automatically
    - Already correct: silent no-op

    Returns True if the entry was written, False on non-Windows or error.
    """
    if not _is_windows():
        return False
    try:
        import winreg

        exe = _get_exe_path()
        value = f'"{exe}" run'

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        ) as key:
            try:
                existing, _ = winreg.QueryValueEx(key, _VALUE_NAME)
                if existing == value:
                    log.debug("Autostart already registered: %s", value)
                    return True
            except FileNotFoundError:
                pass

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, value)
            log.info("Registered autostart: %s", value)
        return True
    except Exception:
        log.warning("Failed to register autostart", exc_info=True)
        return False


def remove_autostart() -> bool:
    """Remove the HKCU Run entry. Returns True if removed or already absent."""
    if not _is_windows():
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            try:
                winreg.DeleteValue(key, _VALUE_NAME)
                log.info("Removed autostart entry")
            except FileNotFoundError:
                log.debug("Autostart entry was already absent")
        return True
    except Exception:
        log.warning("Failed to remove autostart", exc_info=True)
        return False


def is_autostart_registered() -> bool:
    """Check whether the HKCU Run entry exists (any path)."""
    if not _is_windows():
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False
