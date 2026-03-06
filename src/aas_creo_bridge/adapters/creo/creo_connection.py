from pathlib import Path
import subprocess
import time
import creopyson


def connect_to_creoson(max_retries: int = 5, delay: int = 2) -> creopyson.Client:
    """
    Locates the Creoson server relative to this script, starts it,
    and establishes a connection with retry logic.
    """
    # 1. Define paths relative to the current script
    # Path(__file__).resolve().parents[2] points to your project root
    project_root = Path(__file__).resolve().parents[3]
    server_folder = project_root / "creoson"
    creoson_bat = server_folder / "creoson_run.bat"

    # Verify the batch file exists before attempting to start
    if not creoson_bat.exists():
        print(f"Error: Creoson executable not found at: {creoson_bat}")
        return None

    # 2. Launch the Creoson server process
    print(f"Launching Creoson server from: {creoson_bat}")
    try:
        subprocess.Popen(
            [str(creoson_bat)],
            cwd=str(server_folder),
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        print(f"Failed to launch Creoson server process: {e}")
        return None

    # 3. Establish connection with retry logic
    client = creopyson.Client()
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempting to connect to Creoson ({attempt}/{max_retries})...")
            client.connect()
            print("Successfully connected to Creoson.")
            return client
        except Exception:
            if attempt < max_retries:
                time.sleep(delay)
            else:
                print("Connection to Creoson failed after several attempts.")

    return None
