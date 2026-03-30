# Current Capabilities

This project delivers an initial bridge between Asset Administration Shells
(AAS) and CAD systems. The implemented features are aligned with the
engineering and aftersales use cases described in the use case chapter, in
order to demonstrate the practical usability of AAS in real workflows. The
following capabilities are presented in the live demo during the final project
presentation and are used to showcase the use cases.

## General AAS–Creo Bridge

The software supports exporting CAD data from the AAS and importing it into
Creo. It also enables writing parameters onto Creo parts (for example Asset
IDs) so that identifiers are represented directly in the CAD environment.

## Engineering Use Case

For the engineering scenario, the system can export a BOM from Creo as a data
structure modeled after the BOM submodel. Each entity includes volume, mass,
bounding box dimensions, a spatial placement matrix, and all associated Creo
parameters. This provides a structured foundation for engineering analysis and
downstream AAS integration.

## Aftersales Use Case

For the aftersales scenario, activating parts in Creo can open the
corresponding AAS entry in the explorer, where information such as article
numbers can be retrieved. This creates a direct link between CAD interaction
and service-relevant AAS data.
