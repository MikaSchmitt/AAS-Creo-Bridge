# GUI Views

**Path:** `src/aas_creo_bridge/gui/views/`

## Overview

The Views module contains the primary interactive screens of the application. The GUI uses a central stacked widget
approach where different "views" are instantiated once and then shown/hidden based on navigation. These views are Custom
Tkinter (`CTkFrame`) components that manage their own state and coordinate with background services via the app
`context`.

## Main Views

### `HomeView`

- **File:** `home_view.py`
- **Purpose:** The default landing page of the application.
- **Details:** Currently a placeholder view containing a welcome message and logo/branding.

### `ImportView`

- **File:** `import_view.py`
- **Purpose:** Interface for loading `.aasx` packages into the application memory registry.
- **Key Concepts:**
    - Allows users to drag-and-drop or select AASX files.
    - Previews incoming models by showing basic metadata (title, environment version) and extracting a thumbnail if
      available.
    - Contains import confirmation logic that feeds `AASXImportResult` objects to the application's `AASXRegistry`.
- **Integrations:** Requires `import_aasx` from the adapter module and syncs with the `AASXRegistry`.

### `ExplorerView`

- **File:** `explorer_view.py`
- **Purpose:** Acts as a dual-pane explorer for observing registered AAS shells on the left side and their corresponding
  models on the right side.
- **Key Concepts:**
    - **AAS Explorer Side:** Uses a tree view (`ttk.Treeview`) to display the hierarchy of Asset Administration Shells
      loaded into the `AASXRegistry`.
    - **Model Explorer Side:** Uses another tree view to show available 3D models extracted from the shells. Uses the
      `Selection` logic to find the best matching CAD model.
    - Incorporates buttons that synchronize the active AAS model with Creo directly (`sync_aas_to_creo()`).
- **Integrations:** Deeply integrated with the `SynchronizationManager`, `AASXRegistry`, and uses `CreoSessionTracker`
  to dynamically evaluate sync states.

### `ConnectionsView`

- **File:** `connections_view.py`
- **Purpose:** Provides a tabular overview of all active linkages mapped between AAS shells and Creo part models.
- **Key Concepts:**
    - Retrieves linkage state from the `SynchronizationManager`.
    - Displays side-by-side columns: AAS Shell ID against mapped Creo Model Name.
    - Includes a sync all/refresh button that triggers actions across all valid links.
- **Integrations:** Dependent on updates from the `SynchronizationManager`. Registers a UI listener callback to
  automatically refresh the view if the registry or links change behind the scenes.

### `SettingsView`

- **File:** `settings_view.py`
- **Purpose:** General configuration interface for the application.
- **Details:** Currently a placeholder or minimally configured view intended for user preferences or persistent settings
  configuration (e.g., overriding paths, server ports).

## Common Patterns

### Event Listeners

Many views register callbacks directly to the global `AASXRegistry` or `SynchronizationManager` to reload table views or
tree hierarchies asynchronously if the backing data models change.

### Lazy Loading & State Management

Views often override Tkinter events (like `<Map>` or `tkraise`) or implement specific `refresh()` functions so they only
fetch new data or rebuild UI instances when they become active in the main window stack, preventing the complete UI from
rendering simultaneously.

