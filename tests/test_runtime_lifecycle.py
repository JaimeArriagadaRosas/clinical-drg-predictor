from pathlib import Path

from clinical_runtime.lifecycle import PlatformRuntime


def test_product_runtime_manages_only_api_and_web(tmp_path: Path):
    runtime = PlatformRuntime(tmp_path)
    assert tuple(runtime.services) == ("api", "web")
    assert "training" not in runtime.services


def test_shutdown_stops_services_in_reverse_order(tmp_path: Path, monkeypatch):
    runtime = PlatformRuntime(tmp_path)
    calls: list[str] = []

    for name, service in runtime.services.items():
        monkeypatch.setattr(service, "stop", lambda timeout=8.0, name=name: calls.append(name))

    runtime.shutdown()

    assert calls == ["web", "api"]
