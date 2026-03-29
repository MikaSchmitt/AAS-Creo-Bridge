# Installation Guide

There are no binaries released yet. Follow the Developer Guide below to set up a development environment and run the
application from source.

# Getting Started for Developers

## Prerequisites

- Python 3.12
- Git
- Creo Parametric 12 with JLink enabled
- Java 21 or higher (required when not using the embedded JRE option)

## 1) Clone the repository

```powershell
git clone https://github.com/MikaSchmitt/AAS-Creo-Bridge.git
cd AAS-Creo-Bridge
```

## 2) Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3) Install dependencies

```powershell
python .\scripts\setup.py --install-deps --embedded-jre
```

- `--install-deps`: install all necessary python packages
- `--embedded-jre`:This will download a version of creoson with an embedded JRE.
- `--force`: override existing creoson installation.

## 4) Configure IDE

Add `stubs/` to your interpreter search path to enable type hints.

## 5) Run the application

```powershell
python -m src.aas_creo_bridge
```

## Testing

```powershell
pytest
pytest tests\app\test_sync_manager.py

```

## Next

Take a look at the following documentation

- **[Architecture Overview](../architecture/overview.md)** — System design and data flow
