import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Union

import creopyson
from creopyson.exceptions import MissingKey

_logger = logging.getLogger(__name__)


def _stream_process_output(pipe, prefix: str) -> None:
    try:
        for line in iter(pipe.readline, ""):
            _logger.info("%s%s", prefix, line.rstrip())
    finally:
        pipe.close()


def run_creoson_setup(server_folder_path: Path) -> None:
    setup_exe = server_folder_path / "CreosonSetup.exe"
    if not setup_exe.exists():
        raise FileNotFoundError(f"Creoson setup not found: {setup_exe}")

    # Run installer and wait until it exits.
    completed = subprocess.run(
        [str(setup_exe)],  # add installer args if needed
        cwd=str(server_folder_path),
        check=False,
        text=True,
    )

    if completed.returncode != 0:
        raise RuntimeError(f"CreosonSetup.exe failed with exit code {completed.returncode}")


def connect_to_creoson(
        server_folder: Union[str, Path],
        max_retries: int = 5,
        delay: int = 2,
) -> creopyson.Client | None:
    server_folder_path = Path(server_folder)
    creoson_bat = server_folder_path / "creoson_run.bat"

    if not creoson_bat.exists():
        raise FileNotFoundError(f"Creoson executable not found at: {creoson_bat}")

    # check if setvars.bat exists
    setvars_bat = server_folder_path / "setvars.bat"
    if not setvars_bat.exists():
        run_creoson_setup(server_folder_path)

    _logger.info("Launching Creoson server from: %s", creoson_bat)
    try:
        proc = subprocess.Popen(
            [str(creoson_bat)],
            cwd=str(server_folder_path),
            shell=True,  # needed for .bat
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if proc.stdout is not None:
            threading.Thread(
                target=_stream_process_output,
                args=(proc.stdout, "[creoson] "),
                daemon=True,
            ).start()
    except Exception as e:
        raise RuntimeError(f"Failed to launch Creoson server process: {e}") from e

    client = creopyson.Client()
    for attempt in range(1, max_retries + 1):
        status = proc.poll()
        if status is None:
            _logger.info("Creoson server is running")
        else:
            _logger.error("Creoson server exited with status %s", status)
            _logger.error("Creoson server exited prematurely. Check if Creoson is configured correctly.")
            run_creoson_setup(server_folder_path)

        try:
            _logger.info("Attempting to connect to Creoson (%s/%s)...", attempt, max_retries)
            client.connect()
            _logger.info("Successfully connected to Creoson.")
            return client
        except ConnectionError:
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise RuntimeError("Connection to Creoson failed after several attempts.")
        except RuntimeError | MissingKey as e:
            raise RuntimeError(f"Failed to connect to Creoson: {e}") from e
    return None
