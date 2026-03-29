from __future__ import annotations

from aas_creo_bridge.adapters.creo import probe as creoson_probe


class _ClientRunning:
    def __init__(self, port: int = 9056) -> None:
        self.port = port

    def connect(self) -> None:
        return None

    def is_creo_running(self) -> bool:
        return True

    def disconnect(self) -> None:
        return None


class _ClientNotReachable:
    def __init__(self, port: int = 9056) -> None:
        self.port = port

    def connect(self) -> None:
        raise ConnectionError("offline")


class _ClientCreoDown(_ClientRunning):
    def is_creo_running(self) -> bool:
        return False


def test_probe_creoson_status_running_and_connected(monkeypatch) -> None:
    monkeypatch.setattr(creoson_probe.creopyson, "Client", _ClientRunning)

    result = creoson_probe.probe_creoson_status()

    assert result.creoson_running is True
    assert result.creo_connected is True


def test_probe_creoson_status_server_not_running(monkeypatch) -> None:
    monkeypatch.setattr(creoson_probe.creopyson, "Client", _ClientNotReachable)

    result = creoson_probe.probe_creoson_status()

    assert result.creoson_running is False
    assert result.creo_connected is False


def test_probe_creoson_status_creo_not_connected(monkeypatch) -> None:
    monkeypatch.setattr(creoson_probe.creopyson, "Client", _ClientCreoDown)

    result = creoson_probe.probe_creoson_status()

    assert result.creoson_running is True
    assert result.creo_connected is False
