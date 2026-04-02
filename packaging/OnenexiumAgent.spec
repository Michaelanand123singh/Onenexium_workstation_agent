# PyInstaller spec — build from repo root:
#   pip install -e ".[dev]"
#   pyinstaller packaging/OnenexiumAgent.spec
#
# Output: dist/OnenexiumAgent.exe (double-click = run agent; first-time setup opens browser)

import sys
from pathlib import Path

# SPECPATH is the directory that contains this .spec file (e.g. .../packaging).
root = Path(SPECPATH).resolve().parent
src = root / "src"

block_cipher = None

a = Analysis(
    [str(src / "onenexium_agent" / "__main__.py")],
    pathex=[str(src)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "onenexium_agent.collectors.windows",
        "onenexium_agent.collectors.stub",
        "psutil",
        "pydantic_settings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="OnenexiumAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
