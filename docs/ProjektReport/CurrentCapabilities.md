# Current Capabilities

The software now supports exporting CAD files from the AAS and importing them
into Creo. It also supports exporting a BOM from Creo as a data structure modeled
after the BOM submodel. Each entity in that structure includes volume, mass,
bounding box dimensions, a spatial placement matrix, and all associated Creo
parameters.
Parameters can be assigned to parts in Creo (for example to represent Asset IDs),
and these parameters are also retrievable during BOM export.
