# Onenexium workstation agent

Python background agent for **Nexium OS**: periodically records foreground application activity on a laptop and uploads batches to `POST /api/workstation/ingest`.

## Requirements

- Python **3.11+** (for `pip install`; packaged **exe** is optional, see [packaging/README-WINDOWS.md](packaging/README-WINDOWS.md))
- **Windows** for real foreground/idle sampling (other platforms use a stub collector for tests only)

## Install (development)

From this directory:

```bash
pip install -e ".[dev]"
```

## Configure

### A) Browser setup page (recommended for employees)

Run:

```bash
onenexium-agent configure
```

Or **double-click `OnenexiumAgent.exe`** (see Windows packaging doc) — if no token is saved yet, **`run` opens this page automatically**.

- A tab opens to **http://127.0.0.1:&lt;port&gt;/** (localhost only).
- Enter **API base URL** and **ingest token** from **Nexium → Workstation**.
- **Save** sends a test sample to Nexium; only on **success** is config written to:

**`%APPDATA%\OnenexiumAgent\config.json`** (Windows)

### B) Environment variables (IT / MDM)

All settings use the prefix `ONENEXIUM_`. **Environment variables override the JSON file.**

| Variable | Description |
|----------|-------------|
| `ONENEXIUM_API_BASE_URL` | Nexium app origin, e.g. `https://workspace.onenexium.com` (no trailing slash) |
| `ONENEXIUM_INGEST_TOKEN` | Bearer token shown once when a Super Admin registers the device in **Workstation** |
| `ONENEXIUM_SAMPLE_INTERVAL_SECONDS` | Seconds between samples (default `60`) |
| `ONENEXIUM_UPLOAD_INTERVAL_SECONDS` | Seconds between upload attempts (default `300`) |
| `ONENEXIUM_IDLE_THRESHOLD_SECONDS` | Last-input idle threshold (default `120`) |
| `ONENEXIUM_SEND_WINDOW_TITLES` | `true` / `false` — send window titles to the server (default `false`) |
| `ONENEXIUM_PROJECT_ROOT_PREFIXES` | JSON array of path prefixes, e.g. `["C:\\\\dev\\\\onenexium"]` (optional) |
| `ONENEXIUM_PROJECT_TITLE_MARKERS` | JSON array of substrings for title-based detection (default includes `onenexium`, `nexium`) |
| `ONENEXIUM_DATA_DIR` | Optional queue directory (default `%USERPROFILE%\.onenexium-agent`) |

**In-project** is a heuristic: executable path under a configured prefix and/or a title marker in the foreground title (titles can be used for matching even when `ONENEXIUM_SEND_WINDOW_TITLES=false`).

### Auto-open setup after failures

During **`run`**, if uploads fail **3 times in a row**, the same **configure** page opens again so the user can fix URL/token/network without editing JSON by hand.

## Run

Default command (no subcommand) = `run`:

```bash
onenexium-agent
# or
onenexium-agent run
```

Single sample + flush:

```bash
onenexium-agent once
```

## Windows exe (double-click)

See **[packaging/README-WINDOWS.md](packaging/README-WINDOWS.md)** — build `dist/OnenexiumAgent.exe` with PyInstaller (no console window; logs in `%APPDATA%\OnenexiumAgent\agent.log`).

- Double-click = `run`; `OnenexiumAgent.exe configure` = setup only.
- **Keep it running after reboot / Task Manager:** run **`Install-OnenexiumAgentPersistence.ps1`** once (see `packaging/windows/` or monorepo `releases/` after build).

## Nexium OS setup

1. Apply the Prisma migration for `WorkstationDevice` / `WorkstationActivitySample`.
2. Open **Workstation** — use **Cloud API** for the correct **API base URL**.
3. **Super Admin** → **Create device** → copy the ingest token into the agent setup page (or env).

## Compliance

Use only with a clear internal policy, employee notice, and proportionate data collection. This tool does not capture keystrokes or screenshots.

## Tests

```bash
python -m pytest
```
