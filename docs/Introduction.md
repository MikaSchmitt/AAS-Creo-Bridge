# Introduction

## General

In the Mechatronics degree program at Karlsruhe University of Applied Sciences (HKA), students are required to carry out
a joint project under the supervision of a professor. Project topics may be proposed by students themselves or offered
by professors. The present project was initiated and supervised by Prof. Dr. Michael Hoffmeister.

## Topic

The aim of this project is to integrate CAD data into a digital twin. To represent this digital twin in a structured and
standardized manner, the Asset Administration Shell (AAS) is utilized. It serves as a “container” for various documents
associated with CAD data. The AAS is set up and managed with the AASX Package Explorer.

The objective is to implement an exemplary import and export process between CAD data (e.g., asset IDs, BOM structures)
and corresponding AAS structures. User interaction is intended to take place through a graphical user interface (GUI).

## Software Utilized

The CAD software Creo 12 forms the basis of this work. PyCharm serves as the development environment, while Python is
used as the programming language for creating scripts and plugins. The JSON file format enables the extraction of
assembly structures (e.g., BOM data) from the CAD system for subsequent processing.

While Creo and PyCharm are proprietary software products, the AASX Package Explorer is released under the Apache License
2.0. The AASX Package Explorer is fully open source, including its documentation and repository on GitHub (
Markdown/AsciiDoc). The AASX software is a prototype primarily intended for developers.

## Use Cases

At the beginning of this project, several functional areas of a hypothetical industrial company were outlined and
discussed with respect to how the AAS could be applied in each context. Subsequently, the scope was narrowed down to two
specific use cases: Engineering and After-Sales.

### Engineering

#### 1. Scenario and User Role

Robert Redford is a design engineer at an actuator manufacturer. He is responsible for developing a new vacuum gripper.
During the development phase, he must ensure that all relevant requirements from the Machinery Directive, applicable
safety standards, and documentation requirements are fulfilled. These requirements are digitally stored as properties
and documents within the gripper’s AAS.

Robert is looking for a suitable vacuum generator (e.g., suction module) for a new gripper.

#### 2. Workflow

##### Component Selection

Robert checks the requirements stored in the AAS of the vacuum gripper (e.g., safety standards, technical limits). He
searches the supplier’s catalog for a suitable vacuum generator and downloads its AAS.

##### Integration of the AAS

The AAS of the vacuum generator is imported into the AAS of the vacuum gripper. In the AAS editor or directly within the
CAD system, the connections between the gripper and the vacuum generator (e.g., pneumatic, electrical, mechanical) are
defined. The geometry of the vacuum generator is automatically placed within the CAD model of the gripper.

##### Bill of Material (BOM)

After integration, Robert can generate the updated BOM directly in the CAD system. The BOM is automatically updated and
stored as a submodel within the AAS and now includes the new vacuum generator along with all associated data.

#### 3. Benefits

##### Seamless Integration

Components from different manufacturers can be seamlessly integrated because the AAS serves as a standardized exchange
format.

##### Automation

Component integration and BOM updates are performed automatically.

##### Regulatory Compliance

All requirements from the Machinery Directive and applicable safety standards are digitally documented and can be
verified at any time.

##### Lifecycle Transparency

All technical, safety‑related, and sustainability‑related information is centrally managed within the AAS. This creates
full transparency across the entire product lifecycle, from design and operation to maintenance, optimization, and spare
parts management.

### After‑Sales

#### 1. Scenario and User Role

Once the vacuum gripper is in operation, the after‑sales phase begins, including: maintenance, repair, and spare parts
management. Paul Newman, a service technician at the same company, who supports customers in the field. When a
malfunction is reported, such as a sudden loss of vacuum pressure, he uses the digital product data stored in the AAS to
diagnose and resolve the issue efficiently.

The CAD assemblies created during development serve as his central reference. Using these models, together with derived
views such as exploded views and assembly diagrams, Paul can perform maintenance tasks accurately and reliably.

#### 2. Workflow

##### Preparation

A customer reports a sudden loss of vacuum pressure during operation for example. Paul opens the relevant assembly in
Creo, where the corresponding disassembly instructions from the AAS are automatically displayed in a second window.

##### Identification

Paul selects the affected component directly within the CAD model. All relevant metadata, such as part numbers and
material specifications, is automatically retrieved from the AAS. This helps him quickly identify the likely cause of
the pressure loss.

##### Repair

Paul follows the step‑by‑step repair instructions provided through the AAS. These instructions include required tools,
safety considerations, torque values, and all other details needed to replace or repair the faulty component correctly.

##### Feedback

If the same issue occurs repeatedly across multiple service cases, Paul documents it in the after‑sales system. This
feedback is routed through the AAS back to the engineering department, enabling targeted design improvements for future
product iterations.

#### 3. Benefits

##### Increased Efficiency

Service technicians receive all relevant information directly within the CAD system, reducing both repair time and the
likelihood of errors.

##### Traceability

Every service case is clearly documented and can be traced back to the affected assembly and the specific spare part
involved.

##### Feedback Loop

Insights gained during service operations are systematically fed back to the engineering department, enabling targeted
product improvements.

##### Regulatory Compliance

All relevant information on hazardous substances, recyclability, and part interchangeability is available digitally and
supports compliance with regulatory requirements.

##### Automation

The integration of CAD and AAS enables largely automated provisioning and updating of service-related information. 


