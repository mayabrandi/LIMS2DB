
What is a Process Category?
============================

In the project-statusdb context, lims processes are categorised into groups that define, or are used to define a certain type of status-db key in a project database. The categories are specified here. When a new work flow is initialised in lims, the different categories needs to be updated to contain any aditional steps that has not already been included from some other workfrow. 

Adding a work flow.
==========================

If a work flow does not fit with the categories one might have to change the category definitions or ad new categories. This needs to be done in corperation with the developer of project_summary_uppload_LIMS.py. The cathegories are defined in process_categories.py within the objectsDB package.

SEQSTART
==================
These processes are used to set the sequencing_start_date


=== =======================================
ID  process Name
=== =======================================
26	Denature, Dilute and Load Sample (MiSeq) 4.0
23	Cluster Generation (Illumina SBS) 4.0
=== =======================================
    

LIBVALFINISHEDLIB
==================



=== =======================================
ID  process Name
=== =======================================
24	Customer Gel QC
20	CaliperGX QC (DNA)
17	Bioanalyzer QC (Library Validation) 4.0
62	qPCR QC (Library Validation) 4.0
64	Quant-iT QC (Library Validation) 4.0
67	Qubit QC (Library Validation) 4.0
=== =======================================
    

PREPREPSTART
==================
Process/processes that can be defined as a start of the library preparation protocol. If the work flow involves two library preparation protocols, such as for exome captue, only the steps of the first protocol should be given here.


=== =======================================
ID  process Name
=== =======================================
304	Ligate 3' adapters (TruSeq small RNA) 1.0
=== =======================================
    

INITALQCFINISHEDLIB
==================
All processes included in the initial qc protocol for finished libraries, except the aggregation step.


=== =======================================
ID  process Name
=== =======================================
24	Customer Gel QC
20	CaliperGX QC (DNA)
17	Bioanalyzer QC (Library Validation) 4.0
62	qPCR QC (Library Validation) 4.0
64	Quant-iT QC (Library Validation) 4.0
67	Qubit QC (Library Validation) 4.0
=== =======================================
    

AGRINITQC
==================
Aggregation step of the initial qc protocol


=== =======================================
ID  process Name
=== =======================================
9	Aggregate QC (RNA) 4.0
7	Aggregate QC (DNA) 4.0
=== =======================================
    

POOLING
==================
To identify the reagent labels (indexes) of each sample. If multiple pooling steps, the first pooling step after indexing should be specified


=== =======================================
ID  process Name
=== =======================================
308	Library Pooling (TruSeq Small RNA) 1.0
58	Pooling For Multiplexed Sequencing (SS XT) 4.0
255	Library Pooling (Finished Libraries) 4.0
44	Library Pooling (TruSeq Amplicon) 4.0
45	Library Pooling (TruSeq Exome) 4.0
42	Library Pooling (Illumina SBS) 4.0
43	Library Pooling (MiSeq) 4.0
404	Pre-Pooling (Illumina SBS) 4.0
508	Applications Pre-Pooling
506	Pre-Pooling (MiSeq) 4.0
=== =======================================
    

CALIPER
==================



=== =======================================
ID  process Name
=== =======================================
116	CaliperGX QC (RNA)
20	CaliperGX QC (DNA)
=== =======================================
    

WORKSET
==================
To identify the work sets on which the samples has been run. The process used to define a workset for the protocol. 


=== =======================================
ID  process Name
=== =======================================
204	Setup Workset/Plate
=== =======================================
    

PREPEND
==================
Process that can be defined as a end of the library preparation. If more than one library preparation protocol is included in the work flow, only the prep end step of the second protocol should be given here. Used to set the prep finished date.


=== =======================================
ID  process Name
=== =======================================
157	Applications Finish Prep
311	Sample Placement (Size Selection)
456	Purification (ThruPlex)
406	End repair, size selection, A-tailing and adapter ligation (TruSeq PCR-free DNA) 4.0
109	CA Purification
111	Amplify Captured Libraries to Add Index Tags (SS XT) 4.0
=== =======================================
    

DILSTART
==================
These processes are used to set the dilution_and_pooling_start_date


=== =======================================
ID  process Name
=== =======================================
39	Library Normalization (Illumina SBS) 4.0
40	Library Normalization (MiSeq) 4.0
=== =======================================
    

INITALQC
==================
All processes included in the initial qc protocol, except the aggrigation step.


=== =======================================
ID  process Name
=== =======================================
63	Quant-iT QC (DNA) 4.0
65	Quant-iT QC (RNA) 4.0
66	Qubit QC (DNA) 4.0
68	Qubit QC (RNA) 4.0
24	Customer Gel QC
20	CaliperGX QC (DNA)
16	Bioanalyzer QC (DNA) 4.0
18	Bioanalyzer QC (RNA) 4.0
116	CaliperGX QC (RNA)
504	Volume Measurement QC
=== =======================================
    

SUMMARY
==================



=== =======================================
ID  process Name
=== =======================================
356	Project Summary 1.3
=== =======================================
    

LIBVAL
==================
All processes included in the library validation protocol, except the aggregation step. If the work flow involves two library preparation protocols, such as for exome capture, only the steps of the second protocol should be given here.


=== =======================================
ID  process Name
=== =======================================
20	CaliperGX QC (DNA)
17	Bioanalyzer QC (Library Validation) 4.0
62	qPCR QC (Library Validation) 4.0
64	Quant-iT QC (Library Validation) 4.0
67	Qubit QC (Library Validation) 4.0
=== =======================================
    

SEQUENCING
==================
Sequencing


=== =======================================
ID  process Name
=== =======================================
46	MiSeq Run (MiSeq) 4.0
38	Illumina Sequencing (Illumina SBS) 4.0
=== =======================================
    

DEMULTIPLEX
==================



=== =======================================
ID  process Name
=== =======================================
13	Bcl Conversion & Demultiplexing (Illumina SBS) 4.0
=== =======================================
    

PREPSTART
==================
Process/processes that can be defined as a start of the library preparation protocol. The first one of these that are run in lims is used to set the prep start date. If the work flow involves two library preparation protocols, such as for exome capture, the prep start step of the second protocol should be given here. 


=== =======================================
ID  process Name
=== =======================================
407	Fragment DNA (ThruPlex)
10	Aliquot Libraries for Hybridization (SS XT)
117	Applications Generic Process
33	Fragment DNA (TruSeq DNA) 4.0
47	mRNA Purification, Fragmentation & cDNA synthesis (TruSeq RNA) 4.0
308	Library Pooling (TruSeq Small RNA) 1.0
405	RiboZero depletion
=== =======================================
    

AGRLIBVAL
==================
The aggregation step of the library validation protocol


=== =======================================
ID  process Name
=== =======================================
8	Aggregate QC (Library Validation) 4.0
=== =======================================
    

