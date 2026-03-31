# Architecture Overview

This project is structured as a bridge between CAD Systems (currently PTC Creo Parametric) and the Asset Administration
Shell (AAS). It uses an adapter pattern to separate concerns and provide a clean interface for interacting with the CAD
system and the AAS.

## Core Components

### `aas_adapter`

This module provides the necessary interfaces for generating, importing, and manipulating AAS structures building upon
the `basyx.aas` library.

### `aas_creo_bridge`

The central application logic that unifies the CAD processes and user interfaces.

1. **App**: Main context, configuration, and state management.
2. **GUI**: A Tkinter-based user interface enabling visual interaction with the AAS repositories and the CAD system.
3. **Creo_adapter**: Connects to the Creo API. Uses JLink and `creopyson` behind the scenes to extract Bills of
   Materials (BOM), inject properties, and import model files.

## High Level Workflow

The application supports several key workflows:

### 1. Exporting BOM from CAD to AAS

1. The Bridge connects to a running Creo session via Creoson / Jink.
2. The user initiates a BOM extraction from the **GUI**.
3. **Creo_adapter** reads the hierarchical structure and parts information from Creo.
4. The extracted JSON/Dict data is provided to the **aas_adapter**.
5. The Bridge logic generates or updates AAS models (e.g. Submodels like "BillOfMaterial" or "DigitalNameplate").
6. The updated AASX file or repository is saved.

### 2. Exploring AAS

1. The user opens an AASX package or connects to an AAS repository via the **GUI**.
2. The **aas_adapter** parses and loads the Asset Administration Shells, Submodels, and property data.
3. The application displays the hierarchy, allowing the user to inspect properties, relationships, and associated files.

### 3. Importing Models from AAS to CAD

1. While exploring an AAS, the user identifies an attached CAD model file.
2. The user triggers an import action via the **GUI**.
3. The **aas_adapter** extracts the physical file from the AAS environment.
4. The **Creo_adapter** sends commands to Creo to load and open the model in the active session.
