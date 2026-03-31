# Initial Creoson Setup Guide

The AAS-Creo-Bridge relies on **Creoson** to communicate with PTC Creo Parametric. When starting the application or
attempting a connection for the first time, you may need to configure Creoson to ensure it can successfully interact
with your local Creo environment.

## 1. Prerequisites

- **PTC Creo Parametric 12** must be installed on your machine.
- **J-Link** must be enabled in your Creo installation. (Note: This is an optional component during the PTC Creo
  installation process if it was not installed by default).

## 2. Locating and Launching Creoson Setup

If the Bridge cannot establish a connection automatically, the Creoson Setup utility is launched.
There is a chance that the Creoson Setup gets stuck in a loop during startup. If this happens:

1. Kill Creoson Setup from the task manager.
2. Navigate to the `creoson` directory within your application or workspace folder.
3. Delete the `setvars.bat` file.
4. Launch the AAS-Creo-Bridge again.

## 3. Configuring the Creo Launch Path

In the Creoson Setup utility, you have to define the location of Creo Parametric so that Creoson knows how to connect to
the session.

1. Set the Path to Creo Parametric:
    - *Example Path*: `C:\Program Files\PTC\Creo 12.4.0.0\Common Files`
2. Keep the default Setting for the Port
3. Click `Start CREOSON` and close the setup utility.

## 4. Verifying the Connection

1. Launch the AAS-Creo-Bridge application.
2. In the side navigation, go to the **Connection View**.
3. On the right side models that are currently open in Creo should appear.

