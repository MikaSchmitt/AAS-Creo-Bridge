from __future__ import annotations

from dataclasses import dataclass

import creopyson
from creopyson.exceptions import MissingKey

from .config.defaults import DEFAULT_JSON_PORT


@dataclass(slots=True)
class CreosonProbeResult:
    creoson_running: bool
    creo_connected: bool
    details: str


def probe_creoson_status(port: int = DEFAULT_JSON_PORT) -> CreosonProbeResult:
    client = creopyson.Client(port=port)
    creo_connected = False

    try:
        client.connect()
    except (ConnectionError, RuntimeError, MissingKey) as exc:
        return CreosonProbeResult(
            creoson_running=False,
            creo_connected=False,
            details=f"CREOSON not reachable on port {port}: {exc}",
        )

    try:
        creo_connected = bool(client.is_creo_running())
    except (ConnectionError, RuntimeError, MissingKey) as exc:
        return CreosonProbeResult(
            creoson_running=True,
            creo_connected=False,
            details=f"CREOSON reachable, but Creo status query failed: {exc}",
        )
    finally:
        try:
            client.disconnect()
        except Exception:
            pass

    return CreosonProbeResult(
        creoson_running=True,
        creo_connected=creo_connected,
        details="CREOSON reachable; Creo connection status checked.",
    )

