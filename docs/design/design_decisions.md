# Design Decisions

This document outlines the core architectural and technological decisions made during the development of the
AAS-Creo-Bridge. It explains the rationale behind the chosen approaches, frameworks, and tools.

## 1. Companion Application vs. Integrated Plugin

The AAS-Creo-Bridge is designed as a standalone "companion" application that runs alongside PTC Creo Parametric, rather
than as an embedded plugin or integrated toolkit extension running directly inside the Creo process.

### Rationale

* **Technology Stack Flexibility:** Creo plugins are typically written in C/C++ (Creo Toolkit) or Java (J-Link). By
  using a companion app architecture that communicates via an API (Creoson), we were able to write the entire
  application
  logic, data transformation, and GUI in Python. Python offers superior libraries for data manipulation, rapid
  prototyping,
  and interacting with the Asset Administration Shell (via `basyx.aas`).
* **Decoupled Updates:** The companion app can be updated, restarted, and deployed independently of the CAD system.
  There is no need to restart Creo or manage complex internal DLL/JAR loading mechanisms during development or
  deployment.
* **Cross-Domain Interaction:** A standalone application acts as a clear middle-man. It visualizes the AAS domain
  separately from the CAD domain, making it easier for users to understand the mapping and bridge between the two
  environments without cluttering the native Creo user interface.

## 2. Selection of Creoson vs. Creo Toolkit

To bridge the gap between our Python application and PTC Creo, we chose to use **Creoson** (accessed via the `creopyson`
Python wrapper) instead of the native **Creo Toolkit** (C/C++) or **J-Link** (Java) APIs directly.

### Rationale

* **Language Barrier:** The native Creo APIs are heavily tied to C/C++ and Java. Calling native C++ Creo Toolkit
  functions from Python requires complex bindings (such as ctypes, SWIG, or Pybind11) which are difficult to maintain
  and platform-dependent.
* **Microserver Architecture:** Creoson acts as a microserver that exposes Creo's internal J-Link API over standard
  JSON-RPC via HTTP. This modernizes the integration, turning complex CAD API calls into simple, language-agnostic web
  requests.
* **Ease of Use & Community:** Creoson and its Python wrapper, `creopyson`, abstract away many of the low-level
  difficulties of communicating with Creo. Extracting a Bill of Materials (BOM) or injecting a parameter becomes a
  simple
  Python function call returning a dictionary, rather than requiring verbose boilerplate code for memory management and
  Creo session handling.
* **Trade-offs:** While Creoson is incredibly easy to use, it does introduce a slight performance overhead due to the
  HTTP/JSON serialization step compared to direct in-memory C++ Toolkit calls. However, for metadata extraction, BOM
  parsing, and parameter injection (which are the core use cases for this bridge), this overhead is negligible and
  heavily
  outweighed by the reduction in development time and complexity.
* **License:** Creoson is licensed under the MIT License, which is permissive and allows for both personal and
  commercial use without requiring any royalties or distribution of source code. This aligns well with the open-source
  nature of the AAS-Creo-Bridge project and encourages widespread adoption and contribution. To develop an application
  using a Creo Toolkit, a developer license is required. Using Creoson, reduces the barrier of entry for collaborators
  as
  no licenses apart from Creo Parametric have to be acquired to contribute to the project.
* **Feature Set:** Creoson provides a comprehensive set of features for interacting with Creo Parametric, including
  model manipulation, parameter management, and BOM handling. It supports both synchronous and asynchronous operations,
  making it suitable for both real-time and batch processing scenarios. The Creo Toolkits are more extensive and offer
  more advanced features, for manipulating models and allow for an integration into Creo Parametric's native GUI which
  would provide a more seamless user experience and better performance for complex operations.

## 3. Selection of Tkinter as a GUI Framework

The graphical user interface for the AAS-Creo-Bridge is built using **Tkinter**, Python's native GUI toolkit.

### Rationale

* **Zero Dependencies & Built-in:** Tkinter is included with standard Python installations on Windows. This eliminates
  the need to bundle large third-party GUI frameworks, keeping the application's footprint smaller and simplifying the
  build and deployment process (e.g., when packaging with PyInstaller).
* **Sufficient Feature Set:** The application primarily requires standard UI components: tree views (for displaying the
  CAD BOM and AAS hierarchy), property tables, input forms, and progress bars. Tkinter, specifically with the `ttk`
  (Themed Tkinter) extensions, provides all these widgets natively.
* **Simplicity and Speed of Development:** Tkinter is straightforward to implement and well-documented. For an
  application focused heavily on backend transformations (CAD to AAS) rather than highly custom animations or complex
  graphical rendering, Tkinter allowed for rapid development of a functional and clean interface.
* **Trade-offs:** Tkinter's default look and feel can appear slightly dated out-of-the-box compared to modern
  frameworks like PyQt/PySide or web-based electron apps. However, using `ttk` themes helps mitigate this, providing a
  native OS appearance that is more than adequate for a professional engineering utility.

