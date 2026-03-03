from pathlib import Path

def import_model_into_creo(path:Path, source_format:str, target_format:str = "") -> None:
    if not path.exists():
        raise ValueError(f"Path {path} does not exist")
    if source_format in ("prt", "asm"):
        # TODO: use "file_open" to open file in creo
        return

    file_type = ""

    if source_format in (".igs", ".iges"):
        file_type = "IGES"
    if source_format == ".neu":
        file_type = "NEUTRAL"
    if source_format in (".pvz", ".pvs"):
        file_type = "PV"
    elif source_format in (".stp", ".step"):
        file_type = "STEP"
    else:
        raise ValueError(f"Unsupported target format: {target_format}")

    #TODO: import model into Creo
    return