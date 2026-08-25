from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .lifecycle import PlatformRuntime
from .preflight import CheckResult, find_project_root, preflight_ok, run_preflight

app = typer.Typer(no_args_is_help=True, help="Clinical Intelligence Platform developer runtime.")
console = Console()


def _root() -> Path:
    return find_project_root()


def _render_checks(results: tuple[CheckResult, ...]) -> None:
    table = Table(title="Preboot checks")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for result in results:
        table.add_row(result.name, "OK" if result.ok else "FAIL", result.detail)
    console.print(table)


def _require_preflight(root: Path) -> None:
    results = run_preflight(root)
    _render_checks(results)
    if not preflight_ok(results):
        raise typer.Exit(code=1)


@app.command()
def setup() -> None:
    """Install Python and web workspace dependencies using existing toolchains."""
    root = _root()
    commands = (
        ("uv", "sync", "--all-packages", "--group", "dev"),
        ("pnpm", "install"),
    )
    for command in commands:
        console.print(f"Running: {' '.join(command)}")
        subprocess.run(command, cwd=root, check=True)


@app.command()
def preboot() -> None:
    """Validate local prerequisites and application boundaries."""
    _require_preflight(_root())


@app.command()
def run() -> None:
    """Preboot, start local services, and stop them gracefully on termination."""
    root = _root()
    _require_preflight(root)
    runtime = PlatformRuntime(root)
    runtime.install_signal_handlers()
    runtime.start()
    console.print("API: http://127.0.0.1:8000")
    console.print("Web: http://127.0.0.1:5173")
    try:
        runtime.wait()
    except KeyboardInterrupt:
        runtime.shutdown()


@app.command(name="console")
def interactive_console() -> None:
    """Run the platform with a small interactive lifecycle console."""
    root = _root()
    _require_preflight(root)
    runtime = PlatformRuntime(root)
    runtime.install_signal_handlers()
    runtime.start()
    console.print("Commands: status, start <service>, stop <service>, restart <service>, quit")

    try:
        while True:
            raw = console.input("clinical> ").strip()
            if not raw:
                continue
            parts = raw.split()
            command = parts[0].lower()

            if command in {"quit", "exit"}:
                break
            if command == "status":
                table = Table(title="Runtime status")
                table.add_column("Service")
                table.add_column("State")
                table.add_column("PID")
                for name, (running, pid) in runtime.status().items():
                    table.add_row(name, "running" if running else "stopped", str(pid or "-"))
                console.print(table)
                continue
            if command in {"start", "stop", "restart"} and len(parts) == 2:
                service = parts[1]
                if service not in runtime.services:
                    console.print(f"Unknown service: {service}")
                    continue
                getattr(runtime, command)(service)
                continue

            console.print("Unknown command. Use status, start, stop, restart, or quit.")
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    app()
