# Selection

**Path:** `src/aas_adapter/selection.py`

## Overview

The selection module provides a set of utility functions for parsing, filtering, and identifying the most appropriate
physical component models (represented by `FileData` objects) based on their compatibility with consuming applications,
file versions, and required formats.

When an Asset Administration Shell encompasses multiple versions of a 3D model (e.g., Creo native files, STEP files, or
legacy version parts), this module parses their metadata and consuming application requirements to yield the
best-matched file that the CAD adapter or user can handle.

In short, this module does three things:

- Groups extracted file references by their embedded file versions.
- Filters and assesses application compatibility (forward, backward, full, or none).
- Selects the ideal model file dynamically according to prioritized application compatibilities and format fallbacks.

## Key Concepts

### Model Filtering & Consumption

`filter_model_by_app` applies sophisticated version-matching logic (via `_matching_consuming_apps`). It checks whether a
requested application name matches a model's specified consumed applications. Compatibility settings ("forward", "
backward", "none", or "full") determine if the application versions align. For instance, backward compatibility permits
opening an older model file in an updated host application.

### Version Sorting

`group_models_by_version` converts a flat list of models into a dictionary, automatically cataloging them by file
version identifiers. Following this, the `select_best_model` function identifies the highest available file version
across the dataset safely using tuple transformations.

### Smart Selection Strategy

At the core of the module, `select_best_model` orchestrates the extraction process using these policies:

1. First, arrays records by the highest valid file version.
2. Second, scopes down each bucket for models satisfying primary target software compatibilities.
3. Third, if specific consuming application priorities are unmet, leverages raw `FileFormat` backups (e.g., preferring
   STEP derivatives).
4. Ultimately returns the optimal `FileData` definition to materialize.
