from __future__ import annotations

import html
import logging
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

from onenexium_agent.models import utc_now_iso
from onenexium_agent.user_config import get_user_config_path, save_user_config_file
from onenexium_agent.workstation.constants import WORKSTATION_INGEST_PATH

log = logging.getLogger(__name__)


def _page_form(
    *,
    csrf: str,
    api_base_url: str,
    ingest_token: str,
    message: str | None,
    error: str | None,
) -> str:
    msg_html = ""
    if message:
        msg_html = f'<p class="ok">{html.escape(message)}</p>'
    err_html = ""
    if error:
        err_html = f'<p class="err">{html.escape(error)}</p>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Onenexium Agent — Setup</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 36rem; margin: 2rem auto; padding: 0 1rem; }}
  label {{ display: block; margin-top: 1rem; font-weight: 600; }}
  input {{ width: 100%; box-sizing: border-box; margin-top: 0.25rem; padding: 0.5rem; }}
  button {{ margin-top: 1.25rem; padding: 0.5rem 1rem; cursor: pointer; }}
  .ok {{ color: #166534; background: #dcfce7; padding: 0.75rem; border-radius: 6px; }}
  .err {{ color: #991b1b; background: #fee2e2; padding: 0.75rem; border-radius: 6px; }}
  .hint {{ font-size: 0.875rem; color: #555; margin-top: 0.25rem; }}
  code {{ font-size: 0.8rem; }}
</style></head><body>
<h1>Onenexium workstation agent</h1>
<p>Enter the values from <strong>Nexium → Workstation</strong> (Cloud API + device token).</p>
{err_html}{msg_html}
<form method="post" action="/save">
  <input type="hidden" name="csrf" value="{html.escape(csrf)}"/>
  <label for="api_base_url">API base URL</label>
  <input id="api_base_url" name="api_base_url" type="url" required
    placeholder="https://workspace.example.com" value="{html.escape(api_base_url)}"/>
  <p class="hint">No trailing slash — same as <code>ONENEXIUM_API_BASE_URL</code>.</p>
  <label for="ingest_token">Ingest token</label>
  <input id="ingest_token" name="ingest_token" type="password" autocomplete="off" required
    placeholder="Paste token from Workstation" value="{html.escape(ingest_token)}"/>
  <p class="hint">Shown once when an admin registers this PC.</p>
  <button type="submit">Save &amp; close</button>
</form>
<p class="hint">Config file: <code>{html.escape(str(get_user_config_path()))}</code></p>
</body></html>"""


def test_nexium_connection(api_base_url: str, ingest_token: str) -> tuple[bool, str]:
    base = api_base_url.rstrip("/")
    url = f"{base}{WORKSTATION_INGEST_PATH}"
    body = {
        "hostname": "wizard-test",
        "agentVersion": "wizard",
        "samples": [
            {
                "sampledAt": utc_now_iso(),
                "processName": "config-wizard",
                "idle": False,
                "inProjectRoots": False,
            }
        ],
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(
                url,
                json=body,
                headers={
                    "Authorization": f"Bearer {ingest_token}",
                    "Content-Type": "application/json",
                },
            )
        if r.status_code == 200:
            return True, "Connection OK — token accepted."
        if r.status_code == 401:
            return False, "Unauthorized (401): wrong token or device revoked."
        return False, f"Server returned HTTP {r.status_code}: {r.text[:200]}"
    except httpx.RequestError as e:
        return False, f"Network error: {e}"


def run_config_wizard(
    *,
    initial_api_base_url: str = "",
    initial_ingest_token: str = "",
) -> None:
    """
    Blocking: serves a local setup page on 127.0.0.1 and opens the default browser.
    Saves api_base_url + ingest_token to user config on successful POST.
    """
    csrf = secrets.token_urlsafe(16)
    state: dict[str, str | None] = {"message": None, "error": None}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            log.debug("%s - %s", self.address_string(), _format)

        def do_GET(self) -> None:
            if self.path.startswith("/favicon"):
                self.send_response(404)
                self.end_headers()
                return
            if self.path != "/" and not self.path.startswith("/?"):
                self.send_response(404)
                self.end_headers()
                return
            body = _page_form(
                csrf=csrf,
                api_base_url=initial_api_base_url,
                ingest_token=initial_ingest_token,
                message=state["message"],
                error=state["error"],
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path != "/save":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            fields = urllib.parse.parse_qs(raw, keep_blank_values=True)

            def first(name: str) -> str:
                v = fields.get(name, [""])[0]
                return v.strip() if isinstance(v, str) else ""

            if first("csrf") != csrf:
                state["error"] = "Invalid session — refresh the page."
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return

            api = first("api_base_url").rstrip("/")
            token = first("ingest_token")
            if not api or not token:
                state["error"] = "Both fields are required."
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return

            ok, msg = test_nexium_connection(api, token)
            if not ok:
                state["error"] = msg
                state["message"] = None
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return

            save_user_config_file({"api_base_url": api, "ingest_token": token})
            state["message"] = "Saved. You can close this tab."
            state["error"] = None
            body = _page_form(
                csrf=csrf,
                api_base_url=api,
                ingest_token=token,
                message=state["message"],
                error=None,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    for port in range(49200, 49300):
        try:
            server = HTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        raise RuntimeError("No free localhost port for configuration wizard")

    url = f"http://127.0.0.1:{port}/"
    log.info("Opening configuration page: %s", url)
    threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    server.serve_forever()
    server.server_close()
