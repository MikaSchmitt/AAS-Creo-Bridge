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
        path = _resolve_versioned_path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

    if use_workdir:
        try:
            # Set working directory for relative file operations
            client.creo_cd(str(path.parent))
            _logger.info("Working directory changed to: %s", str(path.parent))
        except Exception as e:
            _logger.error("Error setting working directory: %r", e, exc_info=True)
            raise RuntimeError(f"Failed to set working directory: {path.parent}") from e

    file_info = _analyze_path(path)

    try:
        # --- 1. Native Creo Formats ---
        if file_info["is_native"]:
            if use_workdir:
                client.file_open(file_info["open_name"], display=True)
            else:
                client.file_open(file_info["open_name"], dirname=str(path.parent), display=True)
            _logger.info("Successfully opened native file: %s", file_info["open_name"])
            return

        # --- 2. Non-native Formats (Interface Import) ---
        file_type = ""
        if any(ext in file_info["extensions"] for ext in ("stp", "step")):
            file_type = "STEP"
        elif any(ext in file_info["extensions"] for ext in ("igs", "iges")):
            file_type = "IGES"
        elif "neu" in file_info["extensions"]:
            file_type = "NEUTRAL"
        elif any(ext in file_info["extensions"] for ext in ("pvz", "pvs")):
            file_type = "PV"
        else:
            raise ValueError(f"No supported format found in extensions: {file_info['extensions']}")

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


def _resolve_versioned_path(path: Path) -> Path:
    if path.parent is None:
        return path
    candidates = []
    pattern = f"{path.name}.*"
    for candidate in path.parent.glob(pattern):
        if candidate.is_file() and candidate.name.startswith(path.name + "."):
            suffix = candidate.name[len(path.name) + 1 :]
            if suffix.isdigit():
                candidates.append(candidate)
    if not candidates:
        return path
    candidates.sort(key=lambda p: int(p.name[len(path.name) + 1 :]))
    return candidates[-1]


def _analyze_path(path: Path) -> dict[str, object]:
    # Extract extensions (lowercase, without dots)
    extensions = [s.lower().strip(".") for s in path.suffixes]
    is_native = "asm" in extensions or "prt" in extensions
    open_name = _get_open_name(path, extensions)
    return {
        "extensions": extensions,
        "is_native": is_native,
        "open_name": open_name,
    }


def _get_open_name(path: Path, extensions: list[str]) -> str:
    # If the file is versioned (e.g. *.asm.23), use the base *.asm for Creo open
    if len(extensions) >= 2:
        last = extensions[-1]
        prev = extensions[-2]
        if last.isdigit() and prev in {"asm", "prt"}:
            return path.with_suffix("").name
    return path.name

