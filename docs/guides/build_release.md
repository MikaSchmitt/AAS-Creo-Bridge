# Building a Release

## Overview

A **onedir release** is a compiled Python application packaged as a single directory containing the executable and all
dependencies. This is the recommended distribution format for AAS-Creo-Bridge because compare to a **onefile release**
creoson doesn't need to be extracted, which would be very slow.

## Prerequisites

### 1. Virtual Environment

Ensure your Python virtual environment is set up with all dependencies. Refer to the [setup documentation](setup.md)
for more information.

### 2. Install PyInstaller

```cmd
python -m pip install --upgrade pip
python -m pip install pyinstaller
```

### 3. Creoson and JRE

Ensure the creoson binaries are present in the `creoson/` folder. Refer to the [setup documentation](setup.md)
for more information. If the embedded JRE is missing it will also not be included in the build.

## Build the Executable

From the repo root, run:

```powershell
.\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --noconsole --name "AAS-Creo-Bridge" --paths "src" --add-data "creoson;creoson" "src\aas_creo_bridge\__main__.py"
```

**What this does:**

- Compiles Python code to bytecode
- Bundles dependencies into `dist/AAS-Creo-Bridge/_internal/`
- Includes `creoson/` folder
- Creates `dist/AAS-Creo-Bridge/AAS-Creo-Bridge.exe`

## Verify the Build

```powershell
# Check exe exists
Test-Path dist\AAS-Creo-Bridge\AAS-Creo-Bridge.exe

# Verify CREOSON is bundled
Test-Path dist\AAS-Creo-Bridge\_internal\creoson\creoson_run.bat
```

**Expected output:** `True` for both

## Directory Structure

After building, your `dist` folder looks like:

```
dist/
└── AAS-Creo-Bridge/
    ├── AAS-Creo-Bridge.exe           ← Launch this
    ├── _internal/
    │   ├── creoson/                  ← CREOSON runtime
    │   │   ├── creoson_run.bat
    │   │   ├── jre/                  ← Java Runtime
    │   │   ├── plugins/              
    │   │   ├── bridge_settings.json
    │   │   ├── setvars.bat
    │   │   └── ... (JARs, configs, etc.)
    │   ├── python312.dll
    │   ├── base_library.zip
    │   └── ... (all Python libraries)
```

## Running the Application

Simply double-click or run from command line:

```powershell
.\dist\AAS-Creo-Bridge\AAS-Creo-Bridge.exe
```

**First launch:**

- GUI window opens
- If CREOSON is not configured, the Settings tab appears
- Refer to the User Guide for more information on the configuration of CREOSON

## Path Resolution

The application automatically detects whether it's running as a frozen executable or from source:

**Frozen mode** (`.exe` running):

- CREOSON path: `dist\AAS-Creo-Bridge\_internal\creoson`
- Config path: `_internal\creoson\bridge_settings.json`

**Source mode** (running from `src`):

- CREOSON path: `<repo-root>\creoson`
- Config path: `<repo-root>\creoson\bridge_settings.json`

This is handled automatically in:

- `src/aas_creo_bridge/adapters/creo/config/paths.py` – Detects `sys.frozen`
- `src/aas_creo_bridge/app/main.py` – Sets CREOSON path at startup

