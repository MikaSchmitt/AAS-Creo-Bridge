# Introduction 

## General 
In the Mechatronics degree program at Karlsruhe University of Applied Sciences (HKA), students are required to carry out a joint project under the supervision of a professor. Project topics may be proposed by students themselves or offered by professors. The present project was initiated and supervised by Prof. Dr. Michael Hoffmeister.

## Topic
The aim of this project is to integrate CAD data into a digital twin. To represent this digital twin in a structured and standardized manner, the Asset Administration Shell (AAS) is utilized. It serves as a “container” for various documents associated with CAD data. The AAS is set up and managed with the AASX Package Explorer. 

The objective is to implement an exemplary import and export process between CAD data (e.g., asset IDs, BOM structures) and corresponding AASX structures. User interaction is intended to take place through a graphical user interface (GUI). 


##  Software Utilized
The CAD software Creo 12 forms the basis of this work. PyCharm serves as the development environment, while Python is used as the programming language for creating scripts and plugins. The JSON file format enables the extraction of assembly structures (e.g., BOM data) from the CAD system for subsequent processing. 

While Creo and PyCharm are proprietary software products, the AASX Package Explorer is released under the Apache License 2.0. The AASX Package Explorer is fully open source, including its documentation and repository on GitHub (Markdown/AsciiDoc). The AASX software is a prototype primarily intended for developers. 


## Use Cases 
At the beginning of this project, several functional areas of a hypothetical industrial company were outlined and discussed with respect to how the AAS could be applied in each context. Subsequently, the scope was narrowed down to two specific use cases: After-Sales and Engineering.


### After-Sales Phase 
#### 1. Scenario Description
   
  Once the product has been delivered, the after‑sales phase begins, including: maintenance, repair, and spare parts management. The CAD assemblies serve    as the central reference point for all service-related activities. Service technicians use these digital models, along with derived views such as          exploded views and assembly diagrams, to carry out maintenance tasks correctly and reliably. 

#### 2. Workflow 

  ##### Preparation 
  A customer reports a malfunction. The service technician opens the relevant assembly in Creo, and the corresponding disassembly instructions (from the     AAS) are automatically displayed in a second window. 

  ##### Identification 
  The technician selects the affected component directly within the CAD model, and all relevant metadata such as part numbers and material specifications    are displayed automatically. 

  ##### Repair 
  The technician follows the step‑by‑step instructions provided via the AAS. These instructions include information on required tools, safety                considerations, and other relevant aspects. 

  ##### Feedback 
  If a specific issue occurs repeatedly, it is documented in the after‑sales system. This feedback is routed through the AAS back to the engineering         department, enabling design improvements where necessary. 

#### 3. Benefits

  ##### Increased Efficiency
  Service technicians receive all relevant information directly within the CAD system, reducing both repair time and the likelihood of errors.
  
  ##### Traceability
  Every service case is clearly documented and can be traced back to the affected assembly and the specific spare part involved.
  
  ##### Feedback Loop
  Insights gained during service operations are systematically fed back to the engineering department, enabling targeted product improvements.
  
  ##### Regulatory Compliance
  All relevant information on hazardous substances, recyclability, and part interchangeability is available digitally and supports compliance with           regulatory requirements.
  
  ##### Automation
  The integration of CAD and AAS enables largely automated provisioning and updating of service-related information.


