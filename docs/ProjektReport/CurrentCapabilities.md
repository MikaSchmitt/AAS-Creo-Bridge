# Current Capabilities

The project set out to build an initial bridge between Asset Administration
Shells (AAS) and CAD systems, with practical use cases to make the connection
concrete. As implementation progressed, the scope shifted based on the
supervisor's priorities: the original recycling use case was set aside in
favor of a robust BOM export pipeline, which was a particular focus of the
supervisor's vision for the project.

Within that refined scope, the software now supports exporting CAD files from
the AAS and importing them into Creo. It also supports exporting a BOM from
Creo as a data structure modeled after the BOM submodel. Each entity in that
structure includes volume, mass, bounding box dimensions, a spatial placement
matrix, and all associated Creo parameters.

In addition, the tooling allows assigning parameters to parts in Creo (for
example to represent Asset IDs). These parameters are then retrievable during
BOM export, enabling consistent identification across the CAD model and the
resulting AAS data.
