# Windows distribution (double-click friendly)

## What employees get

1. **`dist/OnenexiumAgent.exe`** — built with PyInstaller (one file), **`console=False`** (no black terminal).  
   - **Double-click** = run the agent.  
   - If there is **no saved token**, or uploads **fail 3 times in a row**, a **browser tab** opens to **http://127.0.0.1:&lt;port&gt;/** with a short setup form (API base URL + ingest token from Nexium → Workstation).  
   - Saving runs a **live test** against your Nexium ingest API; only then is config written.
   - **Logs:** `%APPDATA%\OnenexiumAgent\agent.log`

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

Output: `onenexium-workstation-agent/dist/OnenexiumAgent.exe` (root script also copies exe + persistence scripts to `onenexium/releases/`)

Use **Python 3.11–3.13** for production builds if you hit PyInstaller/pydantic warnings on bleeding-edge Python.

## “Always on” for this user (recommended)

Use **`packaging/windows/Install-OnenexiumAgentPersistence.ps1`** (also copied to `releases/` when you run `build-workstation-installer.ps1`). Employee runs it **once** in PowerShell (no Administrator required). It registers:

| Task | Behaviour |
|------|-----------|
| **OnenexiumAgent-Logon** | Starts `OnenexiumAgent.exe run` when this **user signs in** (covers **reboot**). |
| **OnenexiumAgent-Watchdog** | Every **10 minutes**, starts the agent if **no** `OnenexiumAgent` process is running (covers **Task Manager kill**). |

**Uninstall:** `Uninstall-OnenexiumAgentPersistence.ps1`

### What you cannot do (Windows + correct telemetry)

The agent reads the **interactive user’s foreground window**. That only works in the **user’s session**. When the user **fully logs off**, that session ends — **no** supported design keeps capturing *their* desktop while they are logged off. The agent will run again at **next logon**.

A **SYSTEM** Windows Service could run at boot without logon, but it **cannot reliably see the logged-in user’s foreground app** (session isolation). So for your use case, **logon task + watchdog** is the practical maximum.

### Optional: MSI / Inno Setup

Wrap `OnenexiumAgent.exe` in [Inno Setup](https://jrsoftware.org/isinfo.php) or your MDM to copy to `%ProgramFiles%` and register the scheduled task. The app itself does not require an installer if you only distribute the exe + instructions.

## Commands

| Action | Command line |
|--------|----------------|
| Run loop (default) | `OnenexiumAgent.exe` |
| Setup page only | `OnenexiumAgent.exe configure` |
| One shot | `OnenexiumAgent.exe once` |
