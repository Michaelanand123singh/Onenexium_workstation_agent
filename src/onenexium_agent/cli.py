from __future__ import annotations

import argparse
import logging
import sys

from onenexium_agent import __version__
from onenexium_agent.autostart import remove_autostart
from onenexium_agent.config_wizard import run_config_wizard
from onenexium_agent.engine import run_forever, run_once
from onenexium_agent.user_config import load_user_config_file


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(prog="onenexium-agent", description="Nexium workstation telemetry agent")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.set_defaults(func=_cmd_run)

    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("run", help="Loop: sample on an interval and upload batches").set_defaults(func=_cmd_run)

    sub.add_parser(
        "once",
        help="Take one sample and try to flush the queue (good for Task Scheduler)",
    ).set_defaults(func=_cmd_once)

    sub.add_parser(
        "configure",
        help="Open a browser page on this PC to set API URL and ingest token",
    ).set_defaults(func=_cmd_configure)

    sub.add_parser(
        "unregister",
        help="Remove the Windows startup entry and stop auto-starting at logon",
    ).set_defaults(func=_cmd_unregister)

    args = p.parse_args(argv)
    args.func(args)


def _cmd_run(_args: argparse.Namespace) -> None:
    try:
        run_forever()
    except KeyboardInterrupt:
        sys.exit(0)


def _cmd_once(_args: argparse.Namespace) -> None:
    run_once()


def _cmd_configure(_args: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data = load_user_config_file()
    run_config_wizard(
        initial_api_base_url=str(data.get("api_base_url", "")),
        initial_ingest_token=str(data.get("ingest_token", "")),
    )


def _cmd_unregister(_args: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ok = remove_autostart()
    if ok:
        print("Removed startup entry. The agent will no longer start at logon.")
    else:
        print("Could not remove startup entry (may already be absent or non-Windows).")


if __name__ == "__main__":
    main()
