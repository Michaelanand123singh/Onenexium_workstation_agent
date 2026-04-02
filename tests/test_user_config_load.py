import os
from pathlib import Path

import pytest

from onenexium_agent.config import load_settings
from onenexium_agent.user_config import save_user_config_file


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "config.json"
    monkeypatch.setattr(
        "onenexium_agent.user_config.get_user_config_path",
        lambda: path,
    )
    return path


def test_load_settings_prefers_env_over_file(config_path: Path, monkeypatch) -> None:
    for k in list(os.environ):
        if k.startswith("ONENEXIUM_"):
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ONENEXIUM_API_BASE_URL", "https://env.example.com")

    save_user_config_file({"api_base_url": "https://file.example.com", "ingest_token": "fromfile"})

    s = load_settings()
    assert s.api_base_url == "https://env.example.com"
    assert s.ingest_token == "fromfile"


def test_load_settings_from_file_only(config_path: Path, monkeypatch) -> None:
    for k in list(os.environ):
        if k.startswith("ONENEXIUM_"):
            monkeypatch.delenv(k, raising=False)

    save_user_config_file({"api_base_url": "https://only.file", "ingest_token": "tok"})
    s = load_settings()
    assert s.api_base_url == "https://only.file"
    assert s.ingest_token == "tok"
