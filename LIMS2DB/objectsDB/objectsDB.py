#!/usr/bin/env python

"""A module for building up the project objects that build up the project database on 
statusdb. Lims is the main source of information.

In the project-statusdb context, lims processes are categorised into groups that
define, or are used to define a certain type of statusdb KEY in a project 
database. 

The LIMS source of each statusdb KEY is documented here within the function in 
witch the KEY it is set. The documentation frequently referes to the different 
process categories. The process categories are the following:

SEQSTART, LIBVALFINISHEDLIB, PREPREPSTART, INITALQCFINISHEDLIB, AGRINITQC, POOLING, CALIPER, WORKSET, PREPEND, DILSTART, INITALQC, SUMMARY, LIBVAL, SEQUENCING, DEMULTIPLEX, PREPSTART, AGRLIBVAL
 
The categories are set in process_categories.py and their definitions are 
documented in process_categories.rst. There you can alo read about how to add 
or change a process category.

Maya Brandi, Science for Life Laboratory, Stockholm, Sweden.
"""
from genologics.lims import *
import genologics.entities as gent
from genologics.lims_utils import *

import codecs
from process_categories import *
from statusdb.db.utils import *
from functions import *
import os
import couchdb
import time
from datetime import date
import logging

class ProjectDB():
    """Instances of this class holds a dictionary formatted for building up the 
    project database on statusdb. the data comes from different lims
    artifacts and processes."""

    def __init__(self, lims_instance, project_id, samp_db):
        self.lims = lims_instance 
        self.samp_db = samp_db
        self.project = Project(self.lims,id = project_id)
        self.preps = ProcessInfo(self.lims , self.lims.get_processes(
               projectname = self.project.name, type = AGRLIBVAL.values()))
        self.demux = self.lims.get_processes(projectname = self.project.name,
                                                    type = DEMULTIPLEX.values())
        self.demux_procs = ProcessInfo(self.lims, self.demux)
        self.seq = self.lims.get_processes(projectname = self.project.name,
                                                    type = SEQUENCING.values())
        self.seq_procs = ProcessInfo(self.lims, self.seq)
        self._get_project_level_info()
        self._make_DB_samples()
        self._get_sequencing_finished()
        self._get_open_escalations()

    def _get_open_escalations(self):
        # Need Denis input
        escalation_ids = []
        processes = self.lims.get_processes(projectname=self.project.name)
        for p in processes:
            step = gent.Step(self.lims, id = p.id)
            if step.actions.escalation:
                samples_escalated = set()
                if step.actions.escalation['status'] == "Pending":
                    shortid = step.id.split("-")[1]
                    escalation_ids.append(shortid)
        if escalation_ids:
            self.obj['escalations'] = escalation_ids


    def _get_project_level_info(self):
        """
        The following statusdb KEYs are set in this function.

        :project/[KEY]:

        ============    ============    =========== ================
        KEY             lims_element    lims_field  description
        ============    ============    =========== ================ 
        application     Project         Application Project level udf
        samples         Sample          Name        Dict of all samples registered for the project. Keys are sample names.
        open_date       Project         open-date   project field 
        close_date      Project         close-date  project field 
        contact         Researcher      email       project.researcher.email
        project_name    Project         name        project field
        project_id      Project         id          project internal id
        details         Project         udfs        Dict of Project level udfs   
        ============    ============    =========== ================"""

        self.obj = {'source' : 'lims',
                        'application' : None,
                        'samples':{},
                        'open_date' : self.project.open_date,
                        'close_date' : self.project.close_date,
                        'entity_type' : 'project_summary',
                        'contact' : self.project.researcher.email,
                        'project_name' : self.project.name,
                        'project_id' : self.project.id}
        self.obj.update(udf_dict(self.project, PROJ_UDF_EXCEPTIONS, False))
        self.obj['details'] = udf_dict(self.project, PROJ_UDF_EXCEPTIONS)
        self._get_affiliation()
        self._get_project_summary_info()

    def _get_affiliation(self):
        """
        The following statusdb KEYs are set in this function.

        :project/[KEY]:

        ============    ============    =========== ================
        KEY             lims_element    lims_field  description
        ============    ============    =========== ================
        affiliation     Lab             Affiliation project.researcher.lab
        ============    ============    =========== ================"""

        researcher_udfs = dict(self.project.researcher.lab.udf.items())
        if researcher_udfs.has_key('Affiliation'):
            self.obj['affiliation'] = researcher_udfs['Affiliation']


    def _get_project_summary_info(self):
        """
        This will raise a warning if more than one project summary is found, only the first one relayed by the API will be handled
        The following statusdb KEYs are set in this function.

        :project/[KEY]:

        =============== ============    =========== ================
        KEY             lims_element    lims_field  description
        =============== ============    =========== ================
        project_summary Process         udfs        A dict with all Process level udfs fetched from the FIRST process of type SUMMARY that has been run on the project.
        =============== ============    =========== ================"""

        project_summary = self.lims.get_processes(projectname =
                                self.project.name, type = SUMMARY.values())
        if len(project_summary) > 0:
            self.obj['project_summary'] = udf_dict(project_summary[0])
        if len(project_summary) > 1:
            logging.warn('Warning. project summary process run more than once')

    def _get_sequencing_finished(self):
        """
        The following statusdb KEYs are set in this function.
        THe key will only be set if the project has a close date

        :project/[KEY]:

        =================== ============    =========== ================
        KEY                 lims_element    lims_field  description
        =================== ============    =========== ================
        sequencing_finished Process         Finish Date Last sequencing_finish_date where sequencing_finish_date is the 'Finish Date' udf of a SEQUENCING step
        =================== ============    =========== ================"""

        ##   sequencing_finishe should be betched from some other udf in the future
        seq_fin = []
        if self.project.close_date and 'samples' in self.obj.keys():
            for samp in self.obj['samples'].values():
                if 'library_prep' in samp.keys(): 
                    for prep in samp['library_prep'].values():
                        if 'sample_run_metrics' in prep.keys():
                            for run in prep['sample_run_metrics'].values():
                                if 'sequencing_finish_date' in run.keys():
                                    seq_fin.append(run['sequencing_finish_date'])
            if seq_fin:
                self.obj['sequencing_finished'] = max(seq_fin)
            else:
                self.obj['sequencing_finished'] = None

    def _make_DB_samples(self):
        ## Getting sample info
        """
        The following statusdb KEYs are set in this function.

        :project/[KEY]:

        ================    ============    =========== ================
        KEY                 lims_element    lims_field  description
        ================    ============    =========== ================
        first_initial_qc    Process         date-run    First of all (INITALQCFINISHEDLIB if application in FINLIB else INITALQC) steps run on any sample in the project.
        no_of_samples       Project                     Number of registered samples for the project
        samples             Sample          Name        Dict of all samples registered for the project. Keys are sample names. Values are described by the project/samples/[sample] doc.
        ================    ============    =========== ================"""

        samples = self.lims.get_samples(projectlimsid = self.project.id)
        self.obj['no_of_samples'] = len(samples)
        runinfo=self.demux_procs or self.seq_procs 
        if len(samples) > 0:
            procss_per_art = self.build_processes_per_artifact(self.lims,
                                                         self.project.name)
            self.obj['first_initial_qc'] = '3000-10-10'
            for samp in samples:
                sampDB = SampleDB(self.lims,
                                  samp.id,
                                  self.obj['project_name'],
                                  self.samp_db,
                                  self.obj['application'],
                                  self.preps.info,
                                  runinfo.info,
                                  processes_per_artifact = procss_per_art)
                self.obj['samples'][sampDB.name] = sampDB.obj
                try:
                    initial_qc_start_date = self.obj['samples'][sampDB.name]['initial_qc']['start_date']
                    if comp_dates(initial_qc_start_date,
                                  self.obj['first_initial_qc']):
                        self.obj['first_initial_qc'] = initial_qc_start_date
                except:
                    pass
        self.obj = delete_Nones(self.obj)


    def build_processes_per_artifact(self,lims, pname):
        """Constructs a dictionary linking each artifact id with its processes.
        Other artifacts can be present as keys. All processes where the project is
        present should be included. The values of the dictionary is sets, to avoid
        duplicated projects for a single artifact.
        """

        processes = lims.get_processes(projectname = pname)
        processes_per_artifact = {}
        for process in processes:
            for inart, outart in process.input_output_maps:
                if inart is not None:
                    if inart['limsid'] in processes_per_artifact:
                        processes_per_artifact[inart['limsid']].add(process)
                    else:
                        processes_per_artifact[inart['limsid']] = {process}

        return processes_per_artifact

class ProcessInfo():
    """This class takes a list of process type names. Eg 
    'Aggregate QC (Library Validation) 4.0' and forms  a dict with info about 
    all processes of the type specified in runs which the project has gone through.""" 

    def __init__(self, lims_instance, processes):
        self.lims = lims_instance
        self.info = self._get_process_info(processes)

    def _get_process_info(self, processes):
        process_info = {}
        for process in processes:
            process_info[process.id] = {'type' : process.type.name ,
                                'start_date': process.date_run,
                                'samples' : {}}
            in_arts=[]
            for in_art_id, out_art_id in process.input_output_maps:
                in_art = in_art_id['uri']       #these are actually artifacts
                out_art = out_art_id['uri']
                samples = in_art.samples
                if in_art.id not in in_arts:
                    in_arts.append(in_art.id)
                    for samp in samples:
                        if not samp.name in process_info[process.id]['samples']:
                            process_info[process.id]['samples'][samp.name] = {}
                        process_info[process.id]['samples'][samp.name][in_art.id] = [in_art, out_art]
        return process_info


class SampleDB():
    """Instances of this class holds a dictionary formatted for building up the 
    samples objects in the project database on status db. Information comes 
    from different lims artifacts and processes."""

    def __init__(self, lims_instance , sample_id, project_name, samp_db,
                        application = None, AgrLibQCs = [], run_info = [],
                        processes_per_artifact = None): 
        self.lims = lims_instance
        self.samp_db = samp_db
        self.AgrLibQCs = AgrLibQCs
        self.lims_sample = Sample(self.lims, id = sample_id)
        self.name = self.lims_sample.name
        self.application = application
        self.run_info = run_info
        self.processes_per_artifact = processes_per_artifact
        self.obj = {}
        self._get_sample_info()

    def _get_sample_info(self):
        """
        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/[KEY]:

        =========================== ============    =========== ================
        KEY                         lims_element    lims_field  description
        =========================== ============    =========== ================
        scilife_name                Sample          name        ..
        well_location               Artifact        location    ..          ..
        details                     Sample          udfs        A dict with all Sample level udfs
        library_prep                Process                     A dict where the keys are named A, B, etc and represent A-prep, B-prep etc. Preps are named A,B,... and are defined by the date of any PREPSTART step. First date-> prep A, second date -> prep B, etc. These are however not logged into the database until the process AGRLIBVAL has been run on the related artifact.
        first_initial_qc_start_date Process         date-run    If aplication is Finished library this value is feched from the date-run of a the first INITALQCFINISHEDLIB step, otherwise from the date-run of a the first INITALQC step
        first_prep_start_date       Process         date-run    First of all PREPSTART and  PREPREPSTART steps run on the sample
        =========================== ============    =========== ================
        
        :project/samples/[sample id]/library_prep/[prep id]/[KEY]:

        =================== ============    =========== ================
        KEY                 lims_element    lims_field  description
        =================== ============    =========== ================
        sample_run_metrics  Process                     A dict of sample runs where keys have the format: LANE_DATE_FCID_BARCODE, where DATE and FCID: from udf ('Run ID') of the SEQUENCING step. BARCODE: from reagent-labels of output artifact from SEQSTART step. LANE: from the location of the input artifact to the SEQUENCING step.
        =================== ============    =========== ================ """ 

        self.obj['scilife_name'] = self.name
        self.obj['well_location'] = self.lims_sample.artifact.location[1]
        self.obj['details'] = udf_dict(self.lims_sample, SAMP_UDF_EXCEPTIONS)
        self.obj.update(udf_dict(self.lims_sample, SAMP_UDF_EXCEPTIONS, False))
        preps = self._get_preps_and_libval()
        if preps:
            runs = self._get_sample_run_metrics(self.run_info, preps)
            for prep_id in runs.keys():
                if preps.has_key(prep_id):
                    preps[prep_id]['sample_run_metrics'] = runs[prep_id]
            self.obj['library_prep'] = self._get_prep_leter(preps)
        initqc = InitialQC(self.lims, self.name, self.processes_per_artifact, 
                                                            self.application)
        self.obj['initial_qc'] = initqc.set_initialqc_info()
        if self.application in ['Finished library', 'Amplicon with adaptors']:
            category = INITALQCFINISHEDLIB.values()
        else:
            category = INITALQC.values()
        self.obj['first_initial_qc_start_date'] = self._get_firts_day(self.name,
                                                                     category)
        self.obj['first_prep_start_date'] = self._get_firts_day(self.name,
                                    PREPSTART.values() + PREPREPSTART.values())
        self.obj = delete_Nones(self.obj)

    def _get_firts_day(self, sample_name ,process_list, last_day = False):
        """return the date of the first of the processes in process_list that
        is related to sample_name, unless last_day is True. 
        """

        arts = self.lims.get_artifacts(sample_name = sample_name, 
                                        process_type = process_list)
        index = -1 if last_day else 0 
        uniqueDates=set([a.parent_process.date_run for a in arts])
        try:
            return sorted(uniqueDates)[index]
        except IndexError:
            return None

    def _get_barcode(self, reagent_label):
        """Extracts barcode from list of artifact.reagent_labels"""

        if reagent_label:
            try:
                index = reagent_label.split('(')[1].strip(')')
            except:
                index = reagent_label
        else:
            return None
        return index

    def _get_sample_run_metrics(self, demux_info, preps):
        """Input: demux_info - instance of the ProcessInfo class with 
        DEMULTIPLEX processes as argument
        For each SEQUENCING process run on the sample, this function steps 
        backwards in the artifact history of the input artifact of the SEQUENCING 
        process to find the folowing information

        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/library_prep/[prep id]/sample_run_metrics/[samp run id]/[KEY]:

        ================================    ============    =========== ================
        KEY                                 lims_element    lims_field  description
        ================================    ============    =========== ================
        dillution_and_pooling_start_date    Process         date-run    date-run of the first of all DILSTART steps in the artifact history of this SEQUENCING step
        sequencing_start_date               Process         date-run    date-run of the first of all SEQSTART steps in the artifact history of this SEQUENCING step
        sequencing_run_QC_finished          Process         date-run    date-run of this SEQUENCING step
        sequencing_finish_date              Process         Finish Date udf ('Finish Date') of this SEQUENCING step
        sample_run_metrics_id                                           The sample database (statusdb) _id for the sample_run_metrics corresponding to the run, sample, lane in question.
        dem_qc_flag                         Artifact        qc-flag    Qc-flag of the output artifact of the latest of all DEMULTIPLEX steps run in the artifact history of this SEQUENCING step
        seq_qc_flag                         Artifact        qc-flag    Qc-flag of the input artifact to this SEQUENCING step
        ================================    ============    =========== ================""" 

        sample_runs = {}
        for id, run in demux_info.items():
            if run['samples'].has_key(self.name):
                for id , arts in run['samples'][self.name].items():
                    history = gent.SampleHistory(sample_name = self.name, 
                                    output_artifact = arts[1].id,        
                                    input_artifact = arts[0].id,        
                                    lims = self.lims,        
                                    pro_per_art = self.processes_per_artifact)
                    steps = ProcessSpec(history.history, history.history_list, 
                                                             self.application)
                    if self.application in ['Finished library', 'Amplicon with adaptors']:
                        key = 'Finished'
                    elif steps.preprepstart:
                        key = steps.preprepstart['id']
                    elif steps.prepstart:
                        key = steps.prepstart['id'] 
                    else:
                        key = None 
                    if key:
                        lims_run = Process(lims, id = steps.lastseq['id'])
                        run_dict = dict(lims_run.udf.items())
                        if preps[key].has_key('reagent_label') and run_dict.has_key('Finish Date'):
                            try:
                                dem_art = Artifact(lims, id = steps.latestdem['outart'])
                                dem_qc = dem_art.qc_flag
                            except ValueError:
                                #Miseq projects might not have a demultiplexing step here
                                #so the artifact id might be None
                                dem_qc=None
                            seq_art = Artifact(lims, id = steps.lastseq['inart'])
                            lims_run = Process(lims, id = steps.lastseq['id'])
                            samp_run_met_id = self._make_sample_run_id(seq_art, 
                                                           lims_run, preps[key],
                                                          steps.lastseq['type'])
                            if samp_run_met_id and self.samp_db:
                                srmi = find_sample_run_id_from_view(self.samp_db,
                                                                 samp_run_met_id)
                                dpsd = steps.dilstart['date'] if steps.dilstart else None
                                ssd = steps.seqstart['date'] if steps.seqstart else None
                                sfd = lims_run.udf['Finish Date'].isoformat()
                                d = {'sample_run_metrics_id' : srmi,
                                    'dillution_and_pooling_start_date' : dpsd,
                                    'sequencing_start_date' : ssd,
                                    'sequencing_run_QC_finished' : run['start_date'],
                                    'sequencing_finish_date' : sfd,
                                    'dem_qc_flag' : dem_qc,
                                    'seq_qc_flag' : seq_art.qc_flag}
                                d = delete_Nones(d)
                                if not sample_runs.has_key(key):
                                    sample_runs[key] = {}
                                sample_runs[key][samp_run_met_id] = d
        return sample_runs

    def _make_sample_run_id(self, seq_art, lims_run, prep, run_type):
        samp_run_met_id = None
        barcode = self._get_barcode(prep['reagent_label'])
        if run_type == "MiSeq Run (MiSeq) 4.0":
            lane = seq_art.location[1].split(':')[1]
        else:
            lane = seq_art.location[1].split(':')[0]
        if dict(lims_run.udf.items()).has_key('Run ID'):
            run_id = lims_run.udf['Run ID']
            try:
                date = run_id.split('_')[0]
                fcid = run_id.split('_')[3]
                samp_run_met_id = '_'.join([lane, date, fcid, barcode])
            except TypeError: 
                #happens if the History object is missing fields, barcode might be None
                logging.debug(self.name+" ",prep,"-", prep['reagent_label'])
                raise TypeError
        return samp_run_met_id

    def _get_prep_leter(self, prep_info):
        """Get preps and prep names; A,B,C... based on prep dates for 
        sample_name. 
        Output: A dict where keys are prep_art_id and values are prep names."""

        dates = {}
        prep_info_new = {}
        preps_keys = map(chr, range(65, 65+len(prep_info)))
        if len(prep_info) == 1:
            prep_info_new['A'] = prep_info.values()[0]
        else:
            for key, val in prep_info.items():
                if val['pre_prep_start_date']:
                    dates[key] = val['pre_prep_start_date']
                else:
                    dates[key] = val['prep_start_date']
            for i, key in enumerate(sorted(dates,key= lambda x : dates[x])):
                prep_info_new[preps_keys[i]] = delete_Nones(prep_info[key])
        return prep_info_new

    def _get_preps_and_libval(self):
        """
        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/library_prep/[prep id]/[KEY]:

        =========================== ============    =============   ================
        KEY                         lims_element    lims_field      description
        =========================== ============    =============   ================
        prep_status                 Artifact        qc-flag         The qc-flag of the input artifact of the last AGRLIBVAL step      
        reagent_label               Artifact        reagent-label   If the sample went throuh POOLING the reagent_labels must be fetched from the input artifact of the first POOLING step. If the sample did not go through POOLING, the reagent_labels are fetched from the input artifact of the last AGRLIBVAL step in the history 
        =========================== ============    =============   ================
        """

        top_level_agrlibval_steps = self._get_top_level_agrlibval_steps()
        preps = {}
        very_last_libval_key = {}
        for AgrLibQC_id in top_level_agrlibval_steps.keys():
            AgrLibQC_info = self.AgrLibQCs[AgrLibQC_id]
            if AgrLibQC_info['samples'].has_key(self.name):
                for inart in AgrLibQC_info['samples'][self.name].items():
                    inart, outart = inart[1]
                    history = gent.SampleHistory(sample_name = self.name, 
                                        output_artifact = outart.id, 
                                        input_artifact = inart.id, 
                                        lims = self.lims, 
                                        pro_per_art = self.processes_per_artifact)
                    steps = ProcessSpec(history.history, history.history_list, 
                                        self.application)
                    prep = Prep(self.name)
                    prep.set_prep_info(steps, self.application)
                    if not preps.has_key(prep.id2AB) and prep.id2AB:
                        preps[prep.id2AB] = prep.prep_info
                    if prep.pre_prep_library_validations and prep.id2AB:
                        preps[prep.id2AB]['pre_prep_library_validation'].update(
                                              prep.pre_prep_library_validations)
                    if prep.library_validations and prep.id2AB:
                        preps[prep.id2AB]['library_validation'].update(
                                                       prep.library_validations)
                        last_libval_key = max(prep.library_validations.keys())
                        last_libval = prep.library_validations[last_libval_key]
                        in_last = very_last_libval_key.has_key(prep.id2AB)
                        is_last = prep.id2AB in very_last_libval_key and (
                                  last_libval_key > very_last_libval_key[prep.id2AB])
                        if is_last or not in_last:
                            very_last_libval_key[prep.id2AB] = last_libval_key
                            if last_libval.has_key('prep_status'):
                                preps[prep.id2AB]['prep_status'] = last_libval['prep_status']
                            preps[prep.id2AB]['reagent_label'] = self._pars_reagent_labels(steps, last_libval)
        if preps.has_key('Finished'):
            try:
                preps['Finished']['reagent_label'] = self.lims_sample.artifact.reagent_labels[0]
            except IndexError:
                #P821 has nothing here
                logging.warn("No reagent label for artifact {} in sample {}".format(self.lims_sample.artifact.id, self.name))
                preps['Finished']['reagent_label'] = None

            preps['Finished'] = delete_Nones(preps['Finished'])
        
        return preps


    def _pars_reagent_labels(self, steps, last_libval):
        """If the sample went throuh POOLING the reagent_labels must be fetched 
        from the input artifact of the first POOLING step. If the sample did 
        not go through POOLING, the reagent_labels are fetched from the input 
        artifact of the last AGRLIBVAL step in the history"""
        if steps.firstpoolstep:
            inart = Artifact(lims, id = steps.firstpoolstep['inart'])
            if len(inart.reagent_labels) == 1:
                return inart.reagent_labels[0]
        if last_libval.has_key('reagent_labels'): 
            if len(last_libval['reagent_labels']) == 1:
                return last_libval['reagent_labels'][0]
            return None
        return None

    def _get_top_level_agrlibval_steps(self):
        topLevel_AgrLibQC={}
        for AgrLibQC_id, AgrLibQC_info in self.AgrLibQCs.items():
            if AgrLibQC_info['samples'].has_key(self.name):
                topLevel_AgrLibQC[AgrLibQC_id]=[]
                inart, outart = AgrLibQC_info['samples'][self.name].items()[0][1]
                history = gent.SampleHistory(sample_name = self.name, 
                                        output_artifact = outart.id, 
                                        input_artifact = inart.id,
                                        lims = self.lims, 
                                        pro_per_art = self.processes_per_artifact)
                for inart in history.history_list:
                    proc_info =history.history[inart]
                    proc_info = filter(lambda p : 
                             (p['type'] in AGRLIBVAL.keys()),proc_info.values())
                    
                    proc_ids = map(lambda p : p['id'], proc_info) 
                    topLevel_AgrLibQC[AgrLibQC_id] = topLevel_AgrLibQC[AgrLibQC_id] + proc_ids
        for AgrLibQC, LibQC in topLevel_AgrLibQC.items():
            LibQC=set(LibQC)
            if LibQC:
                for AgrLibQC_comp, LibQC_comp in topLevel_AgrLibQC.items():
                    if AgrLibQC_comp != AgrLibQC:
                        LibQC_comp=set(LibQC_comp)
                        if LibQC.issubset(LibQC_comp) and topLevel_AgrLibQC.has_key(AgrLibQC):
                            topLevel_AgrLibQC.pop(AgrLibQC)
        return topLevel_AgrLibQC

class InitialQC():
    """Instances of this class holds a dictionary formatted for building up the 
    initial_qc field per sample in the project database on status db.""" 
    
    def __init__(self, lims_inst ,sample, procs_per_art, application):
        self.lims = lims_inst
        self.processes_per_artifact = procs_per_art
        self.sample_name = sample
        self.initialqc_info = {}
        self.steps = None
        self.application = application

    def _get_initialqc_processes(self):
        outarts = self.lims.get_artifacts(sample_name = self.sample_name,
                                          process_type = AGRINITQC.values())
        if outarts:
            outart = Artifact(self.lims, id = max(map(lambda a: a.id, outarts)))
            latestInitQc = outart.parent_process
            inart = latestInitQc.input_per_sample(self.sample_name)[0].id
            history = gent.SampleHistory(sample_name = self.sample_name, 
                                      output_artifact = outart.id,
                                      input_artifact = inart, lims = self.lims,
                                      pro_per_art = self.processes_per_artifact)
            if history.history_list:
                self.steps = ProcessSpec(history.history, history.history_list,
                                                               self.application)

    def set_initialqc_info(self):
        """
        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/initial_qc/[KEY]: 

        =================== ============    ================    ================
        KEY                 lims_element    lims_field          description
        =================== ============    ================    ================
        start_date          Process         date-run            First of all (INITALQCFINISHEDLIB if application in FINLIB else INITALQC) steps found for in the artifact history of the output artifact of one of the AGRINITQC steps 
        finish_date         Process         date-run            One of the AGRINITQC steps
        initials            Researcher      initials            technician.initials of the last of all (AGRLIBVAL if application in FINLIB else AGRINITQC) steps
        initial_qc_status   Artifact        qc-flag             qc-flag of the input artifact to the last of all (AGRLIBVAL if application in FINLIB else AGRINITQC) steps
        caliper_image       Artifact        content-location    content-location of output Result files of the last of all CALIPER steps in the artifact history of the output artifact of one of the AGRINITQC steps
        =================== ============    ================    ================
        """

        self._get_initialqc_processes()
        if self.steps:
            if self.steps.initialqstart:
                self.initialqc_info['start_date'] = self.steps.initialqstart['date']
            if self.steps.initialqcend:
                inart = Artifact(lims, id = self.steps.initialqcend['inart'])
                process = Process(lims,id = self.steps.initialqcend['id'])
                self.initialqc_info.update(udf_dict(inart))
                initials = process.technician.initials
                self.initialqc_info['initials'] = initials
                self.initialqc_info['finish_date'] = self.steps.initialqcend['date']
                self.initialqc_info['initial_qc_status'] = inart.qc_flag
            if self.steps.latestCaliper:
                self.initialqc_info['caliper_image'] = get_caliper_img(
                                                               self.sample_name,
                                           self.steps.latestCaliper['id'], lims)
        return delete_Nones(self.initialqc_info)


class ProcessSpec():
    """Class to identify to what process category a particular process belongs 
    in the artifact history."""

    def __init__(self, hist_sort, hist_list, application):
        self.application = application
        self.init_qc = INITALQCFINISHEDLIB if application in FINLIB else INITALQC
        self.agr_qc = AGRLIBVAL if application in FINLIB else AGRINITQC
        self.libvalends = []                
        self.libvalend = None               
        self.libvals = []
        self.libvalstart = None
        self.prepend = None                 
        self.prepstarts = []
        self.prepstart = None
        self.prepreplibvalends = []         
        self.prepreplibvalend = None        
        self.prepreplibvals = []
        self.prepreplibvalstart = None
        self.preprepstarts = []             
        self.prepends = []
        self.preprepstart = None
        self.workset = None                 
        self.worksets = []
        self.seqstarts = []
        self.seqstart = None
        self.dilstart = None
        self.dilstarts = []
        self.poolingsteps = []
        self.firstpoolstep = None
        self.demproc = []
        self.latestdem = None
        self.seq = []
        self.lastseq = None
        self.caliper_procs = []
        self.latestCaliper = None
        self.initialqcends = []
        self.initialqcs = []
        self.initialqcend = None
        self.initialqcs = []
        self.initialqstart = None

        self._set_prep_processes(hist_sort, hist_list)

    def _set_prep_processes(self, hist_sort, hist_list):
        hist_list.reverse()
        for inart in hist_list:  
            prepreplibvalends = []
            art_steps = hist_sort[inart]
            # INITALQCEND - get last agr initialqc val step after prepreplibval
            self.initialqcends += filter(lambda pro: pro['type'] in self.agr_qc,
                                                            art_steps.values())
            # INITALQCSTART - get all lib val step after prepreplibval
            self.initialqcs += filter(lambda pro: pro['type'] in self.init_qc,
                                                            art_steps.values())
            #1) PREPREPSTART
            self.preprepstarts += filter(lambda pro: (pro['type'] in 
                            PREPREPSTART and pro['outart']), art_steps.values())
            if self.preprepstarts and not self.prepends: 
                # 2)PREPREPLIBVALSTART PREPREPLIBVALEND
                self.prepreplibvals += filter(lambda pro: (pro['type'] in 
                                                LIBVAL), art_steps.values())
                self.prepreplibvalends += filter(lambda pro: pro['type'] in
                                                AGRLIBVAL, art_steps.values())
            elif self.application in FINLIB: 
                # 6) LIBVALSTART LIBVALEND
                self.libvals += filter(lambda pro: pro['type'] in
                                          LIBVALFINISHEDLIB, art_steps.values())
                self.libvalends += filter(lambda pro: pro['type'] in
                                                AGRLIBVAL, art_steps.values())
            elif self.prepends: 
                # 6) LIBVALSTART LIBVALEND
                self.libvals += filter(lambda pro: pro['type'] in
                                                LIBVAL, art_steps.values())
                self.libvalends += filter(lambda pro: pro['type'] in
                                                AGRLIBVAL, art_steps.values())
            # 4) PREPSTART
            self.prepstarts += filter(lambda pro: (pro['type'] in 
                            PREPSTART) and pro['outart'], art_steps.values()) 
            # 5) PREPEND            - get latest prep end
            self.prepends += filter(lambda pro: (pro['type'] in 
                            PREPEND) and pro['outart'] , art_steps.values())
            # 8) WORKSET            - get worksets
            self.worksets += filter(lambda pro: (pro['type'] in 
                            WORKSET) and pro['outart'], art_steps.values()) 
            # 9) SEQSTART dubbelkolla
            if not self.seqstarts:
                self.seqstarts = filter(lambda pro: (pro['type'] in SEQSTART) 
                                        and pro['outart'], art_steps.values())
            # 10) DILSTART dubbelkolla
            if not self.dilstarts:
                self.dilstarts = filter(lambda pro: (pro['type'] in DILSTART) 
                                        and pro['outart'], art_steps.values())
            # 11) POOLING STEPS
            self.poolingsteps += filter(lambda pro: (pro['type'] in
                                        POOLING), art_steps.values()) 
            # 12) DEMULTIPLEXING
            self.demproc += filter(lambda pro: (pro['type'] in
                                               DEMULTIPLEX), art_steps.values())
            # 13) SEQUENCING
            self.seq += filter(lambda pro: (pro['type'] in
                                                SEQUENCING), art_steps.values())
            # 14) CALIPER
            self.caliper_procs += filter(lambda pro: (pro['type'] in
                                                   CALIPER), art_steps.values())
        self.latestCaliper = get_last_first(self.caliper_procs, last = True)
        self.initialqcend = get_last_first(self.initialqcends, last = True)
        self.initialqstart =  get_last_first(self.initialqcs, last = False)
        self.lastseq = get_last_first(self.seq)
        self.latestdem = get_last_first(self.demproc)
        self.workset = get_last_first(self.worksets) 
        self.libvalstart = get_last_first(self.libvals, last = False)
        self.libvalend = get_last_first(self.libvalends)
        self.prepreplibvalend = get_last_first(self.prepreplibvalends)
        self.prepstart = get_last_first(self.prepstarts, last = False)
        self.prepend = get_last_first(self.prepends)
        self.prepreplibvalstart = get_last_first(self.prepreplibvals, 
                                                            last = False)
        self.preprepstart = get_last_first(self.preprepstarts, last = False)
        self.firstpoolstep = get_last_first(self.poolingsteps, last = False)
        self.dilstart = get_last_first(self.dilstarts, last = False)
        self.seqstart = get_last_first(self.seqstarts, last = False)

class Prep():
    """Instances of this class hold a dictionary formatted for building a
    sample prep in the project database on status db. Each sample can have 
    many preps. Their keys are named A,B,C,etc.""" 
    
    def __init__(self, sample_name):
        self.sample_name=sample_name
        self.prep_info = {
            'reagent_label': None,
            'library_validation':{},
            'pre_prep_library_validation':{},
            'prep_start_date': None,
            'prep_finished_date': None,
            'prep_id': None,
            'workset_setup': None,
            'pre_prep_start_date' : None}
        self.id2AB = None
        self.library_validations = {}
        self.pre_prep_library_validations = {}
        self.lib_val_templ = {
            'start_date' : None,
            'finish_date' : None,
            'well_location' : None,
            'prep_status' : None,
            'reagent_labels' : None,
            'average_size_bp' : None,
            'initials' : None,
            'caliper_image' : None}

    def set_prep_info(self, steps, aplication):
        """
        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/library_prep/[lib prep id]/[KEY]:

        =================== ============    =========== ================
        KEY                 lims_element    lims_field  description
        =================== ============    =========== ================
        prep_start_date     Process         date-run    The date-run of a PREPSTART step
        prep_finished_date  Process         date-run    The date-run of a PREPEND step
        prep_id             Process         id          The lims id of a PREPEND step
        workset_setup       Process         id          The lims id of the last WORKSET step
        pre_prep_start_date Process         date-run    The date-run of process 'Shear DNA (SS XT) 4.0'. Only for 'Exome capture' projects   
        amount_taken_(ng)   Artifact        udf         'Amount Taknd (ng)' of the output artifact of the first PREPSTART and PREPREPSTART steps in the history

        =================== ============    =========== ================
        """

        if aplication in ['Amplicon with adaptors', 'Finished library']:
            self.id2AB = 'Finished'
        else:
            if steps.prepstart:
                self.prep_info['prep_start_date'] = steps.prepstart['date']
            if steps.prepend:
                self.prep_info['prep_finished_date'] = steps.prepend['date']
                self.prep_info['prep_id'] = steps.prepend['id']
            if steps.workset:
                self.prep_info['workset_setup'] = steps.workset['id']
            if steps.preprepstart:
                self.prep_info['pre_prep_start_date'] = steps.preprepstart['date']
                self.id2AB = steps.preprepstart['id']
                if steps.preprepstart['outart']:
                    art = Artifact(lims, id = steps.preprepstart['outart'])
                    self.prep_info.update(udf_dict(art))
            elif steps.prepstart:
                self.id2AB = steps.prepstart['id']
                if steps.prepstart['outart']:
                    art = Artifact(lims, id = steps.prepstart['outart'])
                    self.prep_info.update(udf_dict(art))
        if steps.libvalend:
            self.library_validations = self._get_lib_val_info(steps.libvalends,
                                   steps.libvalstart, steps.latestCaliper)
        if steps.prepreplibvalend:
            self.pre_prep_library_validations = self._get_lib_val_info(
                              steps.prepreplibvalends, steps.prepreplibvalstart)

        
    def _get_lib_val_info(self, agrlibQCsteps, libvalstart, latest_caliper_id = None):
        """
        This function holds for both library_validation and pre_prep_library_validation KEYSs

        The following statusdb KEYs are set in this function.

        :project/samples/[sample id]/library_prep/[lib prep id]/library_validation/[lib val id]/[KEY]:

        =================== ============    =============    ================
        KEY                 lims_element    lims_field       description
        =================== ============    =============    ================
        finish_date         Process         date-run         date-run of the last AGRLIBVAL step in the history
        start_date          Process         date-run         First of all LIBVAL steps found for in the artifact history of the output artifact of one of the last AGRLIBVAL step in the history
        well_location       Artifact        location         location of the input artifact of the last AGRLIBVAL step in the history
        prep_status         Artifact        qc-flag          qc-flag of the input artifact of the last AGRLIBVAL step in the history
        reagent_labels      Artifact        reagent-label    reagent-label of the input artifact of the last AGRLIBVAL step in the history
        initials            Researcher      initials         technician.initials of the last AGRLIBVAL step in the history
        average_size_bp     Artifact        Size (bp)        udf ('Size (bp)') of the input artifact of the last AGRLIBVAL step in the history
        caliper_image       ResultFile      content_location location of the caliper image
        conc_units          Artifact        Conc. Units      udf ('Conc. Units') of the input artifact to the last AGRLIBVAL step in the history
        concentration       Artifact        Concentration    udf ('Concentration') of the input artifact to the last AGRLIBVAL step in the history
        volume_(ul)         Artifact        volume (ul)      udf ('volume (ul)') of the input artifact to the last AGRLIBVAL step in the history
        =================== ============    =============    ================
        """

        library_validations = {}
        start_date = libvalstart['date'] if (libvalstart and 
                                         libvalstart.has_key('date')) else None
        for agrlibQCstep in agrlibQCsteps:
            library_validation = self.lib_val_templ
            inart = Artifact(lims, id = agrlibQCstep['inart'])
            if agrlibQCstep.has_key('date'):
                library_validation['finish_date'] = agrlibQCstep['date']
            library_validation['start_date'] = start_date
            library_validation['well_location'] = inart.location[1]
            library_validation['prep_status'] = inart.qc_flag
            library_validation['reagent_labels'] = inart.reagent_labels
            library_validation.update(udf_dict(inart))
            initials = Process(lims, id = agrlibQCstep['id']).technician.initials
            if initials:
                library_validation['initials'] = initials
            if library_validation.has_key("size_(bp)"):
                average_size_bp = library_validation.pop("size_(bp)")
                library_validation["average_size_bp"] = average_size_bp
            if latest_caliper_id and (Process(lims, id=latest_caliper_id['id'])).date_run >= (Process(lims, id=libvalstart['id']).date_run):
                library_validation["caliper_image"] = get_caliper_img(self.sample_name,
                                                        latest_caliper_id['id'], lims)
            library_validations[agrlibQCstep['id']] = delete_Nones(library_validation)
        return delete_Nones(library_validations) 
