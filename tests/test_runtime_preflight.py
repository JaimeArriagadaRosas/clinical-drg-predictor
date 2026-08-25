from pathlib import Path

from clinical_runtime.preflight import preflight_ok, run_preflight


def test_preflight_reports_missing_toolchain(tmp_path: Path) -> None:
    (tmp_path / "apps" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)
    (tmp_path / "apps" / "api" / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "apps" / "web" / "package.json").write_text("{}\n", encoding="utf-8")

    results = run_preflight(
        tmp_path,
        which=lambda command: "/tool" if command == "uv" else None,
        version_info=(3, 12, 0),
    )

    by_name = {result.name: result for result in results}
    assert by_name["python"].ok is True
    assert by_name["uv"].ok is True
    assert by_name["pnpm"].ok is False
    assert preflight_ok(results) is False
