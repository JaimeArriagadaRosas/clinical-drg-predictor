from __future__ import annotations

import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ServiceSpec:
    name: str
    command: tuple[str, ...]
    cwd: Path


def default_service_specs(root: Path) -> tuple[ServiceSpec, ...]:
    return (
        ServiceSpec(
            name="api",
            command=(
                "uv",
                "run",
                "uvicorn",
                "clinical_api.app:app",
                "--app-dir",
                "apps/api/src",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--reload",
            ),
            cwd=root,
        ),
        ServiceSpec(
            name="web",
            command=(
                "pnpm",
                "--dir",
                "apps/web",
                "run",
                "dev",
                "--",
                "--host",
                "127.0.0.1",
                "--port",
                "5173",
            ),
            cwd=root,
        ),
    )


class ManagedService:
    def __init__(self, spec: ServiceSpec) -> None:
        self.spec = spec
        self.process: subprocess.Popen[str] | None = None

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process is not None else None

    def start(self) -> None:
        if self.running:
            return
        self.process = subprocess.Popen(self.spec.command, cwd=self.spec.cwd, text=True)

    def stop(self, timeout: float = 8.0) -> None:
        if not self.running or self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)


class PlatformRuntime:
    def __init__(self, root: Path, specs: tuple[ServiceSpec, ...] | None = None) -> None:
        self.root = root
        resolved_specs = specs if specs is not None else default_service_specs(root)
        if any(spec.name == "training" for spec in resolved_specs):
            raise ValueError("training belongs to the Training Workbench, not the product runtime")
        self.services = {spec.name: ManagedService(spec) for spec in resolved_specs}
        self._shutting_down = False

    def start(self, name: str | None = None) -> None:
        targets = [self.services[name]] if name else list(self.services.values())
        for service in targets:
            service.start()

    def stop(self, name: str | None = None) -> None:
        targets = [self.services[name]] if name else list(reversed(self.services.values()))
        for service in targets:
            service.stop()

    def restart(self, name: str) -> None:
        self.stop(name)
        self.start(name)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        try:
            self.stop()
        finally:
            self._shutting_down = False

    def status(self) -> dict[str, tuple[bool, int | None]]:
        return {name: (service.running, service.pid) for name, service in self.services.items()}

    def install_signal_handlers(self) -> None:
        def handle_signal(signum: int, _frame: object) -> None:
            self.shutdown()
            raise SystemExit(128 + signum)

        for signal_name in ("SIGINT", "SIGTERM"):
            if hasattr(signal, signal_name):
                signal.signal(getattr(signal, signal_name), handle_signal)

    def wait(self) -> None:
        try:
            while any(service.running for service in self.services.values()):
                time.sleep(0.25)
        finally:
            self.shutdown()
