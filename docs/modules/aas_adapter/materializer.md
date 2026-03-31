# Materializer

**Path:** `src/aas_adapter/materializer.py`

## Overview

The materializer module provides functionality for extracting and preparing physical model files from an Asset
Administration Shell's file storage. It takes file references discovered within an AAS model and extracts them to a
local destination directory, handling both raw files and compressed ZIP archives.

It uses a given `AASXImportResult` (which provides the internal file store), a `FileData` object (which specifies the
model metadata to extract), and an output directory path. The primary output is a `PreparedModelFile` instance
indicating the extracted file path and its recognized format.

In short, this module does three things:

- Locates file contents within the `AASXImportResult`'s file store based on metadata file paths.
- Copies standalone files directly to the output directory or processes ZIP archives to find format-matching files (like
  Creo `.prt`/`.asm` files or `.step` files).
- Returns the resulting path and format of the materialized target file.

## Key Concepts

### File Extractor

The function `materialize_model_file` validates the content type of the file. If the file is of type `application/zip`,
it loads the ZIP archive into memory, inspects its contents, and searches for file extensions that match the expected
`FileFormat` (e.g., Creo Parametric, STEP, or IGES). Once found, it extracts this specific file to the given `out_dir`.

For singular 3D model files (such as `application/step`, `application/octet-stream`, or `model/*`), it simply streams
the file from the AASX file store directly to a new file in the specified output directory.

### Prepared Model

The extraction yields a `PreparedModelFile` dataclass. This wrapper provides other modules (like the Creo adapter)
direct access to the path of the physical file on disk alongside its original known format, allowing subsequent
applications to properly load, interpret, and inject the file into their respective environments.
