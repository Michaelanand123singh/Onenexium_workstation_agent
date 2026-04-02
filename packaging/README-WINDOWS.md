# Windows distribution (double-click friendly)

## What employees get

1. **`dist/OnenexiumAgent.exe`** — built with PyInstaller (one file).  
   - **Double-click** (or Task Scheduler) = run the agent.  
   - If there is **no saved token**, or uploads **fail 3 times in a row**, a **browser tab** opens to **http://127.0.0.1:&lt;port&gt;/** with a short setup form (API base URL + ingest token from Nexium → Workstation).  
   - Saving runs a **live test** against your Nexium ingest API; only then is config written.

2. **Config on disk** (no admin rights needed):  
   `%APPDATA%\OnenexiumAgent\config.json`

Environment variables `ONENEXIUM_*` still **override** the file (useful for MDM).

## Build the exe (IT / release machine)

**Recommended (monorepo root):** copies the binary to `releases/OnenexiumAgent.exe` for sharing.

```powershell
cd "path\to\onenexium"
.\build-workstation-installer.ps1
```

**Or** from `onenexium-workstation-agent/` only:

```powershell
pip install -e ".[dev]"
python -m PyInstaller packaging/OnenexiumAgent.spec --noconfirm
```

Output: `onenexium-workstation-agent/dist/OnenexiumAgent.exe` (root script also copies to `onenexium/releases/`)

Use **Python 3.11–3.13** for production builds if you hit PyInstaller/pydantic warnings on bleeding-edge Python.

## Optional: run at every logon

Task Scheduler → New task → Trigger “At log on” → Action:

- Program: full path to `OnenexiumAgent.exe`  
- Arguments: *(leave empty — defaults to `run`)*

## Optional: proper installer (MSI / Inno Setup)

Wrap `OnenexiumAgent.exe` in [Inno Setup](https://jrsoftware.org/isinfo.php) or your MDM to copy to `%ProgramFiles%` and register the scheduled task. The app itself does not require an installer if you only distribute the exe + instructions.

## Commands

| Action | Command line |
|--------|----------------|
| Run loop (default) | `OnenexiumAgent.exe` |
| Setup page only | `OnenexiumAgent.exe configure` |
| One shot | `OnenexiumAgent.exe once` |
