from onenexium_agent.config import Settings
from onenexium_agent.engine import _apply_project_flag
from onenexium_agent.models import ActivitySample


def test_apply_project_flag_from_title() -> None:
    settings = Settings(
        ingest_token="x",
        project_root_prefixes=[],
        project_title_markers=["onenexium"],
    )
    raw = ActivitySample(
        process_name="Code.exe",
        idle=False,
        in_project_roots=False,
        window_title=None,
        match_title="editor — onenexium — x",
    )
    out = _apply_project_flag(raw, settings)
    assert out.in_project_roots is True
