import io
import logging
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from aas_adapter.importer import AASXImportResult
from aas_adapter.models import FileFormat, FileData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedModelFile:
    extracted_path: Path
    format: FileFormat


def materialize_model_file(aas_reg_entry: AASXImportResult, model: FileData,
                           out_dir: Path) -> PreparedModelFile | None:
    for meta in model.metadata:
        logger.info(
            "%s\ncontent type: %s\nversion: %s\nfile format: %s",
            meta.filepath,
            meta.file_content_type,
            meta.file_version,
            meta.file_format,
        )

        target_file: Path | None = None

        if not meta.filepath in aas_reg_entry.file_store:
            continue

        if meta.file_content_type == "application/zip":
            zip_buf = io.BytesIO()
            aas_reg_entry.file_store.write_file(meta.filepath, zip_buf)
            zip_buf.seek(0)

            found_any = False
            with zipfile.ZipFile(zip_buf, "r") as zf:

                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = info.filename
                    lower = name.lower()

                    # cross-check file ending with expected file format
                    match meta.file_format.format_name:
                        case "Creo Parametric":
                            if not re.search(r"\.(prt|asm)(\.\d+)?", lower):
                                continue
                        case "STEP":
                            if not re.search(r"\.ste?p", lower):
                                continue
                        case "IGES":
                            if not re.search(r"\.ige?s", lower):
                                continue
                        case _:
                            logger.warning("Unknown file format: %s", meta.file_format.format_name)
                            continue

                    found_any = True
                    target_name = Path(name).name
                    target_file = out_dir / target_name
                    with zf.open(info, "r") as src, target_file.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    logger.info("  Found and saved file from zip: %s", target_file.resolve())

            if not found_any:
                logger.info("  Zip processed in-memory, but no 3d model files were found inside.")

        elif (meta.file_content_type == "application/step" or
              meta.file_content_type == "application/octet-stream" or
              "model/" in meta.file_content_type):
            target_file = out_dir / Path(meta.filepath).name
            with target_file.open("wb") as out:
                aas_reg_entry.file_store.write_file(meta.filepath, out)
            logger.info("  Extracted to: %s", target_file.resolve())

        if target_file is not None:
            return PreparedModelFile(target_file, meta.file_format)
    return None
