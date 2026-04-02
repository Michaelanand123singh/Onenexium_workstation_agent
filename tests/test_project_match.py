from onenexium_agent.project_match import in_company_project, normalize_path_prefixes


def test_normalize_path_prefixes() -> None:
    assert normalize_path_prefixes([r"C:\Dev\Foo", ""]) == [r"c:\dev\foo"]


def test_title_marker() -> None:
    assert (
        in_company_project(
            exe_path=None,
            window_title="Cursor — onenexium — README.md",
            path_prefixes=[],
            title_markers=["onenexium"],
        )
        is True
    )


def test_exe_prefix() -> None:
    assert (
        in_company_project(
            exe_path=r"C:\Dev\onenexium\app\node.exe",
            window_title="",
            path_prefixes=[r"c:\dev\onenexium"],
            title_markers=[],
        )
        is True
    )


def test_no_match() -> None:
    assert (
        in_company_project(
            exe_path=r"C:\Windows\explorer.exe",
            window_title="Documents",
            path_prefixes=[r"c:\dev\onenexium"],
            title_markers=["onenexium"],
        )
        is False
    )
