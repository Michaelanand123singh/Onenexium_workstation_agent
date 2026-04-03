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

## Auto-start at logon (built-in)

The agent **self-registers** on first successful run. It writes a per-user `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` entry (`OnenexiumAgent`) that launches `"<exe-path>" run` at Windows logon. This is the same mechanism used by Slack, Discord, and Steam — no admin rights needed, visible in Task Manager > Startup.

- If the exe is moved to a different folder, the next run updates the path automatically.
- To remove: `OnenexiumAgent.exe unregister` (or delete the entry from Task Manager > Startup).

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

## Extra resilience: watchdog (optional)

The built-in registry Run key handles reboots. For extra protection against Task Manager kills, you can optionally run **`Install-OnenexiumAgentPersistence.ps1`** once. This adds a 10-minute watchdog Scheduled Task that restarts the agent if it's not running. No Administrator needed.

| Task | Behaviour |
|------|-----------|
| **OnenexiumAgent-Logon** | Starts `OnenexiumAgent.exe run` when this **user signs in** (redundant with registry entry, but harmless). |
| **OnenexiumAgent-Watchdog** | Every **10 minutes**, starts the agent if **no** `OnenexiumAgent` process is running (covers **Task Manager kill**). |

**Uninstall watchdog:** `Uninstall-OnenexiumAgentPersistence.ps1`

### What you cannot do (Windows + correct telemetry)

The agent reads the **interactive user's foreground window**. That only works in the **user's session**. When the user **fully logs off**, that session ends — **no** supported design keeps capturing *their* desktop while they are logged off. The agent will run again at **next logon**.

A **SYSTEM** Windows Service could run at boot without logon, but it **cannot reliably see the logged-in user's foreground app** (session isolation). So for your use case, **logon task + watchdog** is the practical maximum.

### Optional: MSI / Inno Setup

Wrap `OnenexiumAgent.exe` in [Inno Setup](https://jrsoftware.org/isinfo.php) or your MDM to copy to `%ProgramFiles%` and register the scheduled task. The app itself does not require an installer if you only distribute the exe + instructions.

## Commands

| Action | Command line |
|--------|----------------|
| Run loop (default) | `OnenexiumAgent.exe` |
| Setup page only | `OnenexiumAgent.exe configure` |
| One shot | `OnenexiumAgent.exe once` |
| Remove auto-start | `OnenexiumAgent.exe unregister` |
