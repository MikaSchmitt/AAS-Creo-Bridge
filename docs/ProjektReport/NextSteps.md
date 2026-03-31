# Next Steps

## Open Code Items

Several areas are still implemented as placeholders and need to be completed.
This includes the GUI menu actions (Open/Save/Export/Validate/Connect/Disconnect/Sync) and some of
the synchronization and linking logic in the `Connections` view. These items block a stable end-to-end
workflow and should be prioritized.

## Functional Extensions

To make accessing AASs easier the option to connect to a Repository could be added to the Import View. Placeholders for
this functionality already exist.

At the moment, BOMs are only fetched from Creo as a structure (for example a
JSON/dict from Creoson). The next step is to write this data into the AAS and
model it as appropriate submodels. A second core function should be the direct
import of CAD models from Creo into an AAS, including storing the files in the
AASX package and referencing them in the relevant submodels.
For model import, a planned enhancement is to place parts not only at the
coordinate origin but also insert them into an existing assembly at defined
positions.
