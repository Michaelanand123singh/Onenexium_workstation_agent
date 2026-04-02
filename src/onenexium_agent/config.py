from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from onenexium_agent.user_config import load_user_config_file

_ENV_KEYS: dict[str, str] = {
    "api_base_url": "ONENEXIUM_API_BASE_URL",
    "ingest_token": "ONENEXIUM_INGEST_TOKEN",
    "sample_interval_seconds": "ONENEXIUM_SAMPLE_INTERVAL_SECONDS",
    "upload_interval_seconds": "ONENEXIUM_UPLOAD_INTERVAL_SECONDS",
    "idle_threshold_seconds": "ONENEXIUM_IDLE_THRESHOLD_SECONDS",
    "send_window_titles": "ONENEXIUM_SEND_WINDOW_TITLES",
    "project_root_prefixes": "ONENEXIUM_PROJECT_ROOT_PREFIXES",
    "project_title_markers": "ONENEXIUM_PROJECT_TITLE_MARKERS",
    "data_dir": "ONENEXIUM_DATA_DIR",
    "log_level": "ONENEXIUM_LOG_LEVEL",
}

_FILE_KEYS = tuple(_ENV_KEYS.keys())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ONENEXIUM_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: str = Field(
        default="http://localhost:3000",
        description="Nexium app origin, no trailing slash",
    )
    ingest_token: str = Field(default="", description="Bearer token from Workstation UI")

    sample_interval_seconds: int = Field(default=60, ge=10, le=3600)
    upload_interval_seconds: int = Field(default=300, ge=30, le=86400)
    idle_threshold_seconds: int = Field(default=120, ge=5, le=3600)
    send_window_titles: bool = Field(default=False)

    project_root_prefixes: list[str] = Field(
        default_factory=list,
        description="Windows paths; exe path under any prefix counts as in-project",
    )
    project_title_markers: list[str] = Field(
        default_factory=lambda: ["onenexium", "nexium"],
        description="If any marker appears in the window title, counts as in-project",
    )

    data_dir: Path | None = Field(
        default=None,
        description="SQLite queue directory; default ~/.onenexium-agent",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("ingest_token", mode="before")
    @classmethod
    def strip_token(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    def resolved_data_dir(self) -> Path:
        if self.data_dir is not None:
            return self.data_dir.expanduser()
        return Path.home() / ".onenexium-agent"


def load_settings() -> Settings:
    """
    Environment variables override values from the user config file.
    File: %APPDATA%\\OnenexiumAgent\\config.json (Windows) or ~/.config/onenexium-agent/config.json
    """
    file_data = load_user_config_file()
    kwargs: dict = {}
    for key in _FILE_KEYS:
        env_var = _ENV_KEYS[key]
        if os.environ.get(env_var) is not None and os.environ.get(env_var) != "":
            continue
        if key not in file_data:
            continue
        val = file_data[key]
        if key == "data_dir" and isinstance(val, str):
            kwargs[key] = Path(val)
        else:
            kwargs[key] = val
    return Settings(**kwargs)
