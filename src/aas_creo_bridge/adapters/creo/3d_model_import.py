

def import_model_to_creo(client, path):
    """Setzt das Arbeitsverzeichnis und öffnet die Datei in Creo."""
    file_dir = os.path.dirname(path)
    file_fullname = os.path.basename(path)
    # Entferne die Versionsnummer (z.B. .10) für den Creo-Befehl
    clean_model_name = re.sub(r'\.\d+$', '', file_fullname)

    try:
        # Verzeichnis wechseln
        client._creoson_post("creo", "cd", {"dirname": file_dir})
        # Modell öffnen
        client.file_open(clean_model_name, display=True)
        print(f"Modell '{clean_model_name}' erfolgreich importiert.")
        return clean_model_name
    except Exception as e:
        print(f"Fehler beim Import: {e}")
        return None
