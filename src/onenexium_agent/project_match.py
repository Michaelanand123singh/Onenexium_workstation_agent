from __future__ import annotations


def normalize_path_prefixes(prefixes: list[str]) -> list[str]:
    out: list[str] = []
    for p in prefixes:
        s = (p or "").strip().replace("/", "\\")
        if not s:
            continue
        out.append(s.lower())
    return out


def in_company_project(
    *,
    exe_path: str | None,
    window_title: str | None,
    path_prefixes: list[str],
    title_markers: list[str],
) -> bool:
    """
    Heuristic: true if the executable path is under a configured prefix (Windows, case-insensitive)
    or if any marker appears in the window title (case-insensitive).
    """
    markers = [m.strip().lower() for m in title_markers if m.strip()]
    if window_title and markers:
        t = window_title.lower()
        if any(m in t for m in markers):
            return True

    if exe_path and path_prefixes:
        low = exe_path.lower().replace("/", "\\")
        for pref in path_prefixes:
            if pref and low.startswith(pref):
                return True
    return False
