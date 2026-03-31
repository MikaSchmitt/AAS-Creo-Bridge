# Troubleshooting Guide

When integrating different systems like CAD software and AAS instances, several common issues can arise. This guide
provides solutions to frequently encountered problems.

## 1. Connection Failures with PTC Creo

### Symptom: The Bridge cannot connect to Creoson

- **Is Creo running?** Ensure a valid PTC Creo session is active.
- **J-Link Missing:** Ensure that J-Link is installed and registered with your PTC Creo installation. If J-Link is
  absent, Creoson cannot communicate with Creo. Re-run the PTC Creo installer and ensure "J-Link" is checked.
- **Incorrect Startup Path:** Ensure your `setvars.bat` points to the correct installation folder of
  `PTC Creo Parametric`.
  Refer to the [Creoson Setup Guide](creoson_setup.md).

## 2. Java Runtime Errors

### Symptom: Creoson crashes or fails to start with Java errors.

- **Missing JRE:** Ensure you have Java 21+ installed on your system or that the embedded JRE option was used during
  setup.
- **Architecture Mismatch:** Ensure you are using the 64-bit version of Java if your operating system and Creo are
  64-bit.

## 3. AASX Import / Parsing Issues

### Symptom: Importing an AASX file fails or shows empty contents.

- **Corrupted File:** Try opening the AASX file in [twinfix](https://twinfix.twinsphere.io/) to verify its integrity.
- **Unsupported Specification Version:** The Bridge relies on `basyx.aas`. Ensure the `.aasx` package was generated
  adhering to a supported version of the Asset Administration Shell specifications (V3.0+).

