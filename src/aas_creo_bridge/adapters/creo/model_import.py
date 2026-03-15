from pathlib import Path
import logging

import creopyson

_logger = logging.getLogger(__name__)

def import_model_into_creo(
    client: creopyson.Client,
    path: Path,
    *,
    use_workdir: bool = False,
) -> None:
    """
    Automatically detects the format from file extensions and
    safely opens or imports the model into Creo.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if use_workdir:
        try:
            # Set working directory
            client.creo_cd(str(path.parent))
            _logger.info("Working directory changed to: %s", str(path.parent))
        except Exception as e:
            _logger.error("Error setting working directory: %r", e, exc_info=True)
            raise RuntimeError(f"Failed to set working directory: {path.parent}") from e

    # Extract all extensions (lowercase, without dots)
    extensions = [s.lower().strip('.') for s in path.suffixes]

    try:
        # --- 1. Native Creo Formats ---
        if "asm" in extensions or "prt" in extensions:
            if use_workdir:
                client.file_open(path.name, display=True)
            else:
                client.file_open(path.name, dirname=str(path.parent), display=True)
            _logger.info("Successfully opened native file: %s", path.name)
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
            raise ValueError(f"No supported format found in extensions: {extensions}")

        # Execute interface import for non-native files.
        # This call returns the imported Creo model name (e.g. *.prt or *.asm).
        imported_model_name = client.interface_import_file(
            filename=path.name,
            file_type=file_type,
            dirname=None if use_workdir else str(path.parent),
            new_name=path.name[: -len(''.join(path.suffixes))]
        )  # Use filename without extensions as model name
        client.file_open(
            imported_model_name,
            dirname=None if use_workdir else str(path.parent),
            display=True,
        )
        _logger.info("Successfully imported and opened %s model: %s", file_type, imported_model_name)


    except Exception as e:
        # Catching any Creoson or connection errors to prevent program crash
        _logger.error("Failed to import/open model '%s': %r", path.name, e, exc_info=True)
        raise RuntimeError(f"Failed to import/open model '{path.name}'") from e

