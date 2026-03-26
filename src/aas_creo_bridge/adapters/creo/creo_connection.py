import subprocess
import time
from pathlib import Path
from typing import Union

import creopyson
from creopyson.exceptions import MissingKey

from aas_creo_bridge.config import validate_setvars_bat


class SetvarsConfigurationError(RuntimeError):
    """Raised when setvars.bat is missing or invalid for CREOSON startup."""


def connect_to_creoson(
        server_folder: Union[str, Path],
        max_retries: int = 5,
        delay: int = 2,
) -> creopyson.Client | None:
    """
    Starts the Creoson server from the provided folder and connects with retry logic.

    :raises FileNotFoundError: If the Creoson batch file does not exist.
    :raises RuntimeError: If the server process cannot be launched or connection fails.
    """
    # 1. Define paths relative to the provided server folder
    server_folder_path = Path(server_folder)
    creoson_bat = server_folder_path / "creoson_run.bat"
    setvars_bat = server_folder_path / "setvars.bat"

    # Verify the batch file exists before attempting to start
    if not creoson_bat.exists():
        raise FileNotFoundError(f"Creoson executable not found at: {creoson_bat}")

    setvars_ok, setvars_error = validate_setvars_bat(setvars_bat)
    if not setvars_ok:
        raise SetvarsConfigurationError(setvars_error or f"Invalid setvars.bat at: {setvars_bat}")

    # 2. Launch the Creoson server process
    print(f"Launching Creoson server from: {creoson_bat}")
    try:
        subprocess.Popen(
            [str(creoson_bat)],
            cwd=str(server_folder_path),
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        raise RuntimeError(f"Failed to launch Creoson server process: {e}") from e

    # 3. Establish connection with retry logic
    client = creopyson.Client()
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempting to connect to Creoson ({attempt}/{max_retries})...")
            client.connect()
            print("Successfully connected to Creoson.")
            return client
        except ConnectionError:
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise RuntimeError("Connection to Creoson failed after several attempts.")
        except RuntimeError | MissingKey as e:
            raise RuntimeError(f"Failed to connect to Creoson: {e}") from e
    return None
