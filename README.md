# CAD-AAS Bridge

A tool for integrating CAD data from Creo into an Asset Administration Shell (AAS) to enable structured storage,
synchronization, and further processing.

# Project Overview

This project enables the import and export of CAD data, including part information and BOM structures, between Creo and
an Asset Administration Shell (AAS). The interaction is handled through a graphical user interface (GUI).

# Main Functions

- Extracting a BOM (bill of materials) from a CAD part
- Structured storage of CAD data within an AAS
- Importing and exporting CAD data via the AAS
- Synchronizing data between CAD software and the AAS
- GUI‑based operation of the tool

# Function overview between CAD software

| Feature                                            | Creo      | Siemens NX |
|----------------------------------------------------|-----------|------------|
| Importing a 3D model from an AAS into CAD software | Planned   | Planned    |
| Exporting a BOM from CAD software into an AAS      | Supported | Planned    |
| Embedding the AAS ID in the 3D model               | Supported | Planned    |
| Assigning AAS IDs to a list of 3D models           | Supported | Planned    |

For detailed instructions on specific CAD systems:

- [Creo Integration Guide](docs/user_guides/creo.md)
- Siemens NX Guide (Coming Soon)

# Graphical User Interface (GUI)

The application provides several views, each covering different functional areas.

## Import View

- Opening and importing AASX files
- Integrating external repositories
- Overview of all imported AASs
- Displaying relevant AAS information

## Connection View

- Managing the connection between CAD software and the AAS
- Overview of existing links
- Configuring synchronization settings
- Starting import and export processes
