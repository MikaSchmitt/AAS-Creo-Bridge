# GUI Components

**Path:** `src/aas_creo_bridge/gui/`

## Overview

The GUI application is built with Custom Tkinter (`customtkinter`), providing a modern look and feel over standard
Tkinter. It acts as the primary user interface for monitoring Asset Administration Shells (AAS), resolving parts
mapping, and triggering synchronization processes to Creo Parametric.

The main components deal with layout and global management (`MainWindow`), side navigation (`LeftNav`), footer
information (`StatusBar`), and supplementary dialogs (`LogWindow`).

## Main Window Structure

### `MainWindow`

**File:** `main_window.py`

The primary application shell. It initializes the main Custom Tkinter loop, binds the views onto the frame stack, and
orchestrates interactions.

- **Initialization:**
    - Instantiates the `AASXRegistry`, `SynchronizationManager`, and starts the `CreoSessionTracker` from the
      application context.
    - Generates the fixed UI elements (the left navigation sidebar and the bottom status bar).
    - Pre-loads all main view frames (`HomeView`, `ImportView`, `ExplorerView`, `ConnectionsView`, `SettingsView`).
- **Navigation Logic:**
    - The `MainWindow` contains `show_view(view_name)`. It handles hiding the current active view, raising the targeted
      frame, invoking standard refresh callbacks on the view if required, and visually highlighting the active button on
      the sidebar.
- **Window Management:**
    - Includes standard boilerplate such as configuring the minimum window size, setting the application icon, and
      scaling options.

## Supplementary Elements

### Sidebar Navigation (`LeftNav`)

**Path:** `src/aas_creo_bridge/gui/widgets/left_nav.py`

- The `LeftNav` is a vertical persistent panel on the left side of the window.
- **Key Concepts:**
    - Generates navigation buttons pointing to all available views.
    - Takes a callback parameter `nav_callback(view_name)` that signals the `MainWindow` to switch the active view when
      a button is clicked.
    - Maintains state of the active button, updating its appearance (e.g., changing text or background color) to
      indicate the active tab.

### Bottom Status Bar (`StatusBar`)

**Path:** `src/aas_creo_bridge/gui/widgets/status_bar.py`

- The `StatusBar` is fixed at the base of the `MainWindow`.
- **Purpose:** Provide live feedback on backend service states and recent application events to the user.
- **Key Concepts:**
    - **Creo Tracker Indication:** Shows whether the `CreoSessionTracker` successfully observes a running instance of
      Creo and the actively selected file format or CAD model.
    - **Logging Output:** Subscribes to the context's `LogStore` to echo the latest log message natively into the status
      bar's label. Clicking this label typically brings up the full `LogWindow`.
    - Also displays generic application status updates, version info, or errors without needing an intrusive dialog box.

### General Interactions

Views inside the main window send signals to the main modules via global instances instantiated from the app `context`
rather than having instances passed down through complex prop drilling.

### Pop-up Windows (`LogWindow`)

**Path:** `src/aas_creo_bridge/gui/views/log_window.py`

- A secondary `CTkToplevel` window that displays the full active log stream.
- **Key Concepts:**
    - Integrates with `LogStore` from `context`. It binds a text box component that appends and scrolls continuously as
      new application events occur.
    - Includes a UI toggle (e.g., auto-scroll or filter settings).
    - Can be spawned via an explicit UI button or a click on the status bar.

## Patterns and Theming

- The UI applies `customtkinter` settings early (color theme, dark/light mode switches usually via
  `set_appearance_mode`).
- Layout grids heavily prefer responsive columns via `grid_columnconfigure` assigning varying weights.

