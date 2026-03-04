import subprocess
import os
import time
import creopyson

def connect_to_creoson():
    """Startet den Server und stellt die Verbindung her."""
    creoson_bat = os.path.join(CREOSON_FOLDER, "creoson_run.bat")
    subprocess.Popen([creoson_bat], cwd=CREOSON_FOLDER, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

    c = creopyson.Client()
    for i in range(5):
        try:
            c.connect()
            print("Verbindung zu Creoson erfolgreich.")
            return c
        except:
            print(f"Verbindungsversuch {i + 1} fehlgeschlagen...")
            time.sleep(2)
    return None
