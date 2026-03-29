from __future__ import annotations

from pathlib import Path

from aas_creo_bridge.adapters.creo.creo_connection import connect_to_creoson

CREOSON_DIR = Path(__file__).resolve().parents[2] / "creoson"


def _can_run_creoson() -> bool:
    if not (CREOSON_DIR / "creoson_run.bat").exists():
        return False
    if not (CREOSON_DIR / "setvars.bat").exists():
        return False
    return True


def test_connect_to_creoson_starts_and_connects() -> None:
    if not _can_run_creoson():
        raise RuntimeError("Creoson setup not available for integration test.")
    client = connect_to_creoson(CREOSON_DIR, max_retries=5, delay=2)
    assert client is not None
