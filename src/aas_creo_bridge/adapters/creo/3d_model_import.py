from pathlib import Path
import creopyson

def import_model_into_creo(client: creopyson.Client, path: Path) -> None:
    """
    Automatically detects the format from file extensions and
    safely opens or imports the model into Creo.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    try:
        # Set working directory
        client.creo_cd(str(path.parent))
    except Exception as e:
        print(f"Error setting working directory: {e}")
        return

    # Extract all extensions (lowercase, without dots)
    extensions = [s.lower().strip('.') for s in path.suffixes]

    try:
        # --- 1. Native Creo Formats ---
        if "asm" in extensions or "prt" in extensions:
            client.file_open(path.name, display=True)
            print(f"Successfully opened native file: {path.name}")
            return

        # --- 2. Non-native Formats (Interface Import) ---
        file_type = ""
        if any(ext in extensions for ext in ("stp", "step")):
            file_type = "STEP"
        elif any(ext in extensions for ext in ("igs", "iges")):
            file_type = "IGES"
        elif "neu" in extensions:
            file_type = "NEUTRAL"
        elif any(ext in extensions for ext in ("pvz", "pvs")):
            file_type = "PV"
        else:
            print(f"No supported format found in extensions: {extensions}")
            return

        # Execute interface import for non-native files
        client.interface_import_file(
            filename=path.name,
            file_type=file_type, 
            new_name=path.stem
        ) # Use filename without the last extension as model name
        print(f"Successfully imported {file_type} model: {path.name}")

    except Exception as e:
        # Catching any Creoson or connection errors to prevent program crash
        print(f"Failed to import/open model '{path.name}': {e}")

