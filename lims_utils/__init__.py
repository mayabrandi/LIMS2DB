INITALQCFINISHEDLIB = {'24' : 'Customer Gel QC',
    '62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0'}
INITALQC ={'63' : 'Quant-iT QC (DNA) 4.0',
    '65' : 'Quant-iT QC (RNA) 4.0',
    '66' : 'Qubit QC (DNA) 4.0',
    '68' : 'Qubit QC (RNA) 4.0',
    '24' : 'Customer Gel QC',
    '20' : 'CaliperGX QC (DNA)',
    '16' : 'Bioanalyzer QC (DNA) 4.0',
    '18' : 'Bioanalyzer QC (RNA) 4.0',
    '116' : 'CaliperGX QC (RNA)',
    '504' : 'Volume Measurement QC'}
AGRINITQC = {'7' : 'Aggregate QC (DNA) 4.0',
    '9' : 'Aggregate QC (RNA) 4.0'}
PREPREPSTART = {'74': 'Shear DNA (SS XT) 4.0',
    '304' : "Ligate 3' adapters (TruSeq small RNA) 1.0"}
POOLING = {'42': "Library Pooling (Illumina SBS) 4.0",
    '43': "Library Pooling (MiSeq) 4.0",
    '44': "Library Pooling (TruSeq Amplicon) 4.0",
    '45': "Library Pooling (TruSeq Exome) 4.0",
    '58': "Pooling For Multiplexed Sequencing (SS XT) 4.0",
    '255': "Library Pooling (Finished Libraries) 4.0",
    '308': "Library Pooling (TruSeq Small RNA) 1.0",
    '404': "Pre-Pooling (Illumina SBS) 4.0",
    '506': "Pre-Pooling (MiSeq) 4.0",
    '508': "Applications Pre-Pooling"}
PREPSTART = {'10' : 'Aliquot Libraries for Hybridization (SS XT)',
    '47' : 'mRNA Purification, Fragmentation & cDNA synthesis (TruSeq RNA) 4.0',
    '33' : 'Fragment DNA (TruSeq DNA) 4.0',
    '407' : 'Fragment DNA (ThruPlex)',
    '308': 'Library Pooling (TruSeq Small RNA) 1.0',
    '117' : 'Applications Generic Process',
    '405' : 'RiboZero depletion'}
PREPEND = {'157': 'Applications Finish Prep',
    '109' : 'CA Purification',
    '456' : 'Purification (ThruPlex)',
    '111' : 'Amplify Captured Libraries to Add Index Tags (SS XT) 4.0',
    '406' : 'End repair, size selection, A-tailing and adapter ligation (TruSeq PCR-free DNA) 4.0',
    '311': 'Sample Placement (Size Selection)'}
LIBVAL = {'62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0'}
LIBVALFINISHEDLIB = {'62' : 'qPCR QC (Library Validation) 4.0',
    '64' : 'Quant-iT QC (Library Validation) 4.0',
    '67' : 'Qubit QC (Library Validation) 4.0',
    '20' : 'CaliperGX QC (DNA)',
    '17' : 'Bioanalyzer QC (Library Validation) 4.0',
    '24' : 'Customer Gel QC'}
AGRLIBVAL = {'8': 'Aggregate QC (Library Validation) 4.0'}
SEQSTART = {'23':'Cluster Generation (Illumina SBS) 4.0',
    '26':'Denature, Dilute and Load Sample (MiSeq) 4.0'}

DILSTART = {'40' : 'Library Normalization (MiSeq) 4.0',
    '39' : 'Library Normalization (Illumina SBS) 4.0'}
SEQUENCING = {'38' : 'Illumina Sequencing (Illumina SBS) 4.0',
    '46' : 'MiSeq Run (MiSeq) 4.0'}
WORKSET = {'204' : 'Setup Workset/Plate'}
SUMMARY = {'356' : 'Project Summary 1.3'}
DEMULTIPLEX={'13' : 'Bcl Conversion & Demultiplexing (Illumina SBS) 4.0'}

FINLIB = ['Finished library', 'Amplicon']
PROJ_UDF_EXCEPTIONS = ['customer_reference','uppnex_id','reference_genome','application']
SAMP_UDF_EXCEPTIONS = ['customer_name','reads_requested_(millions)','min_reads',
    'm_reads','dup_rm','status_auto','status_manual','average_size_bp','incoming_qc_status']

CALIPER={'20' : 'CaliperGX QC (DNA)','116' : 'CaliperGX QC (RNA)'}
