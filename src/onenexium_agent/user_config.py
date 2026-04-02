from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

CONFIG_DIR_NAME = "OnenexiumAgent"
CONFIG_FILE_NAME = "config.json"


def get_agent_data_dir() -> Path:
    """Directory for config.json, agent.log, watchdog script, etc."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / CONFIG_DIR_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "onenexium-agent"
    return Path.home() / ".config" / "onenexium-agent"


def get_user_config_path() -> Path:
    """Per-user JSON config (survives upgrades; not in Program Files)."""
    return get_agent_data_dir() / CONFIG_FILE_NAME


def get_agent_log_path() -> Path:
    return get_agent_data_dir() / "agent.log"


def load_user_config_file() -> dict[str, Any]:
    path = get_user_config_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_user_config_file(updates: dict[str, Any]) -> None:
    path = get_user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load_user_config_file()
    for k, v in updates.items():
        if v is None or v == "":
            current.pop(k, None)
        else:
            current[k] = v
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
