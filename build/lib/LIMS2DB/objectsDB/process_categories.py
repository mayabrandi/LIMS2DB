INITALQCFINISHEDLIB = {'Description':'All processes included in the initial qc protocol for finished libraries, except the aggregation step.',
    '24' : 'Customer Gel QC',
    '62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0'}
INITALQC ={'Description':'All processes included in the initial qc protocol, except the aggrigation step.',
    '63' : 'Quant-iT QC (DNA) 4.0',
    '65' : 'Quant-iT QC (RNA) 4.0',
    '66' : 'Qubit QC (DNA) 4.0',
    '68' : 'Qubit QC (RNA) 4.0',
    '24' : 'Customer Gel QC',
    '20' : 'CaliperGX QC (DNA)',
    '16' : 'Bioanalyzer QC (DNA) 4.0',
    '18' : 'Bioanalyzer QC (RNA) 4.0',
    '116' : 'CaliperGX QC (RNA)',
    '504' : 'Volume Measurement QC'}
AGRINITQC = {'Description':'Aggregation step of the initial qc protocol',
    '7' : 'Aggregate QC (DNA) 4.0',
    '9' : 'Aggregate QC (RNA) 4.0'}
PREPREPSTART = {'Description':'Process/processes that can be defined as a start of the library preparation protocol. If the work flow involves two library preparation protocols, such as for exome captue, only the steps of the first protocol should be given here.',
    '304' : "Ligate 3' adapters (TruSeq small RNA) 1.0"}
POOLING = {'Description':'To identify the reagent labels (indexes) of each sample. If multiple pooling steps, the first pooling step after indexing should be specified',
    '42': "Library Pooling (Illumina SBS) 4.0",
    '43': "Library Pooling (MiSeq) 4.0",
    '44': "Library Pooling (TruSeq Amplicon) 4.0",
    '45': "Library Pooling (TruSeq Exome) 4.0",
    '58': "Pooling For Multiplexed Sequencing (SS XT) 4.0",
    '255': "Library Pooling (Finished Libraries) 4.0",
    '308': "Library Pooling (TruSeq Small RNA) 1.0",
    '404': "Pre-Pooling (Illumina SBS) 4.0",
    '506': "Pre-Pooling (MiSeq) 4.0",
    '508': "Applications Pre-Pooling"}
PREPSTART = {'Description':'Process/processes that can be defined as a start of the library preparation protocol. The first one of these that are run in lims is used to set the prep start date. If the work flow involves two library preparation protocols, such as for exome capture, the prep start step of the second protocol should be given here. ',
    '10' : 'Aliquot Libraries for Hybridization (SS XT)',
    '47' : 'mRNA Purification, Fragmentation & cDNA synthesis (TruSeq RNA) 4.0',
    '33' : 'Fragment DNA (TruSeq DNA) 4.0',
    '407' : 'Fragment DNA (ThruPlex)',
    '308': 'Library Pooling (TruSeq Small RNA) 1.0',
    '117' : 'Applications Generic Process',
    '405' : 'RiboZero depletion'}
PREPEND = {'Description':'Process that can be defined as a end of the library preparation. If more than one library preparation protocol is included in the work flow, only the prep end step of the second protocol should be given here. Used to set the prep finished date.',
    '157': 'Applications Finish Prep',
    '109' : 'CA Purification',
    '456' : 'Purification (ThruPlex)',
    '111' : 'Amplify Captured Libraries to Add Index Tags (SS XT) 4.0',
    '406' : 'End repair, size selection, A-tailing and adapter ligation (TruSeq PCR-free DNA) 4.0',
    '311': 'Sample Placement (Size Selection)'}
LIBVAL = {'Description':'All processes included in the library validation protocol, except the aggregation step. If the work flow involves two library preparation protocols, such as for exome capture, only the steps of the second protocol should be given here.',
    '62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0'}
LIBVALFINISHEDLIB = {'Description':'',
    '62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0',
    '24' : 'Customer Gel QC'}
AGRLIBVAL = {'Description':'The aggregation step of the library validation protocol',
    '8': 'Aggregate QC (Library Validation) 4.0'}
SEQSTART = {'Description':'These processes are used to set the sequencing_start_date',
    '23':'Cluster Generation (Illumina SBS) 4.0',
    '26':'Denature, Dilute and Load Sample (MiSeq) 4.0'}
DILSTART = {'Description':'These processes are used to set the dilution_and_pooling_start_date',
    '40' : 'Library Normalization (MiSeq) 4.0',
    '39' : 'Library Normalization (Illumina SBS) 4.0'}
SEQUENCING = {'Description':'Sequencing',
    '38' : 'Illumina Sequencing (Illumina SBS) 4.0',
    '46' : 'MiSeq Run (MiSeq) 4.0'}
WORKSET = {'Description':'To identify the work sets on which the samples has been run. The process used to define a workset for the protocol. ',
    '204' : 'Setup Workset/Plate'}
SUMMARY = {'Description':'',
    '356' : 'Project Summary 1.3'}
DEMULTIPLEX={'Description':'',
    '13' : 'Bcl Conversion & Demultiplexing (Illumina SBS) 4.0'}
CALIPER = {'Description':'',
    '20' : 'CaliperGX QC (DNA)',
    '116' : 'CaliperGX QC (RNA)'}



FINLIB = ['Finished library', 'Amplicon']
PROJ_UDF_EXCEPTIONS = ['customer_reference','uppnex_id','reference_genome','application']
SAMP_UDF_EXCEPTIONS = ['customer_name','reads_requested_(millions)','min_reads',
    'm_reads','dup_rm','status_auto','status_manual','average_size_bp','incoming_qc_status']



PROCESSCATEGORIES = {'INITALQCFINISHEDLIB' : INITALQCFINISHEDLIB, 
                     'INITALQC':INITALQC,
                     'AGRINITQC':AGRINITQC,
                     'PREPREPSTART':PREPREPSTART,
                     'POOLING':POOLING,
                     'PREPSTART':PREPSTART,
                     'PREPEND':PREPEND,
                     'LIBVAL':LIBVAL,
                     'LIBVALFINISHEDLIB':LIBVALFINISHEDLIB,
                     'AGRLIBVAL':AGRLIBVAL,
                     'SEQSTART':SEQSTART,
                     'DILSTART':DILSTART,
                     'SEQUENCING':SEQUENCING,
                     'WORKSET':WORKSET,
                     'SUMMARY':SUMMARY,
                     'DEMULTIPLEX':DEMULTIPLEX,
                     'CALIPER':CALIPER}
