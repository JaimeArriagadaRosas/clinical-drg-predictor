from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


def find_project_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    for path in (candidate, *candidate.parents):
        if (path / "pyproject.toml").is_file() and (path / "apps").is_dir():
            return path
    raise RuntimeError("Could not locate the repository root from the current directory.")


def run_preflight(
    root: Path,
    *,
    which: Callable[[str], str | None] = shutil.which,
    version_info: tuple[int, ...] | None = None,
) -> tuple[CheckResult, ...]:
    version = version_info or tuple(sys.version_info[:3])
    checks = [
        CheckResult(
            name="python",
            ok=version >= (3, 11),
            detail=f"Python {'.'.join(str(part) for part in version)}",
        ),
        CheckResult(
            name="uv",
            ok=which("uv") is not None,
            detail="uv available" if which("uv") else "uv is not available on PATH",
        ),
        CheckResult(
            name="pnpm",
            ok=which("pnpm") is not None,
            detail="pnpm available" if which("pnpm") else "pnpm is not available on PATH",
        ),
        CheckResult(
            name="api",
            ok=(root / "apps" / "api" / "pyproject.toml").is_file(),
            detail="apps/api boundary present",
        ),
        CheckResult(
            name="web",
            ok=(root / "apps" / "web" / "package.json").is_file(),
            detail="apps/web boundary present",
        ),
    ]
    return tuple(checks)


def preflight_ok(results: tuple[CheckResult, ...]) -> bool:
    return all(result.ok for result in results if result.required)
