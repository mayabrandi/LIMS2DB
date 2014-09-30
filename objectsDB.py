#!/usr/bin/env python

"""A module for building up the project objects that build up the project database on 
statusdb with lims as the main source of information.

Maya Brandi, Science for Life Laboratory, Stockholm, Sweden.
"""
import codecs
from genologics.lims import *
import genologics.entities as gent
from lims_utils import *
from scilifelab.db.statusDB_utils import *
from helpers import *
import os
import couchdb
import bcbio.pipeline.config_utils as cl
import time
from datetime import date
import logging

###  Functions ###

def udf_dict(element, exeptions = [], exclude = True):
    """Takes a lims element and tertuns a dictionary of its udfs, where the udf 
    names are trensformed to statusdb keys (underscore and lowercase).
    
    exeptions and exclude = False - will return a dict with only the exeptions
    exeptions and exclude = True - will return a dict without the exeptions  

    Arguments:
        element     lims element (Sample, Artifact, Process, Project...)
        exeptions   list of exception udf keys (underscore and lowercase)
        exlude      (True/False)"""

    udf_dict = {}
    for key, val in element.udf.items():
        key = key.replace(' ', '_').lower().replace('.','')
        try: val = val.isoformat()
        except: pass
        if key in exeptions and not exclude:
            udf_dict[key] = val
        elif key not in exeptions and exclude:
            udf_dict[key] = val
    return udf_dict

def get_last_first(process_list, last=True):
    returned_process=None
    for pro in process_list:
        if (not returned_process) \
        or (pro.get('date')>returned_process.get('date') and last) \
        or (pro.get('date')<returned_process.get('date') and not last):
            returned_process= pro
    return returned_process

def get_caliper_img(sample_name, caliper_id):
    caliper_image = None
    try:
        last_caliper = Process(lims,id = caliper_id)
        outarts = last_caliper.all_outputs()
        for out in outarts:
            s_names = [p.name for p in out.samples]
            if (sample_name in s_names and out.type == "ResultFile"):
                files = out.files
                for f in files:
                    if ".png" in f.content_location:
                        caliper_image = f.content_location
    except TypeError:
        #Should happen when no caliper processes are found
        pass
    return caliper_image

### Classes  ###

class ProjectDB():
    """Instances of this class holds a dictionary formatted for building up the 
    project database on statusdb. Source of information come from different lims
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
        self._get_project_level_info()
        self._make_DB_samples()
        self._get_sequencing_finished()

    def _get_project_level_info(self):
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
        researcher_udfs = dict(self.project.researcher.lab.udf.items())
        if researcher_udfs.has_key('Affiliation'):
            self.obj['affiliation'] = researcher_udfs['Affiliation']


    def _get_project_summary_info(self):
        project_summary = self.lims.get_processes(projectname =
                                self.project.name, type = SUMMARY.values())
        if len(project_summary) > 0:
            self.obj['project_summary'] = udf_dict(project_summary[0])
        if len(project_summary) > 1:
            print 'Warning. project summary process run more than once'

    def _get_sequencing_finished(self):
        """Finish Date = last seq date if proj closed. Will be removed and 
        feched from lims."""
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
        samples = self.lims.get_samples(projectlimsid = self.project.id)
        self.obj['no_of_samples'] = len(samples)
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
                                  self.demux_procs.info,
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
    all processes of the type specified in runs which the project has gon through.

    info = {24-8460:{ 
              'start_date'
              'samples':{'P424_111':{in_art_id1 : [in_art1, out_art1],
                         in_art_id2: [in_art2, out_art2]},
                     'P424_115': ...},
                       ...},
        '24-8480':...}"""
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
    samples in the project database on status db. Source of information come 
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
        if self.application in ['Finished library', 'Amplicon']:
            chategory = INITALQCFINISHEDLIB.values()
        else:
            chategory = INITALQC.values()
        self.obj['first_initial_qc_start_date'] = self._get_firts_day(self.name,
                                                                     chategory)
        self.obj['first_prep_start_date'] = self._get_firts_day(self.name,
                                    PREPSTART.values() + PREPREPSTART.values())
        self.obj = delete_Nones(self.obj)

    def _get_firts_day(self, sample_name ,process_list, last_day = False):
        """process_list is a list of process type names, sample_name is a 
        sample name :)"""
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
        bacward in the artifact history of the input artifact of the SEQUENCING 
        process to find the folowing information:

        dillution_and_pooling_start_date  date-run of DILSTART step
        sequencing_start_date             date-run of SEQSTART step
        sequencing_run_QC_finished        date-run of SEQUENCING step
        sequencing_finish_date            udf ('Finish Date') of SEQUENCING step
        sample_run_metrics_id             The sample database (statusdb) _id for
                                          the sample_run_metrics corresponding 
                                           to the run, sample, lane in question.
        samp_run_met_id = lane_date_fcid_barcode            
            date and fcid:  from udf ('Run ID') of the SEQUENCING step. 
            barcode:        The reagent-lables of the input artifact of process 
                            type AGRLIBVAL
            lane:           from the location of the input artifact to the 
                            SEQUENCING step    
        preps are defined as the id of the PREPSTART step in the artifact 
        history. If appllication== Finished library, prep is defined as 
        "Finnished". These keys are used to connect the seqeuncing steps to the 
        correct preps."""
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
                    if self.application in ['Finished library', 'Amplicon']:
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
                            dem_art = Artifact(lims, id = steps.latestdem['outart'])
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
                                    'dem_qc_flag' : dem_art.qc_flag,
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
        """"""
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
    """"""
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
            outart = Artifact(lims, id = max(map(lambda a: a.id, outarts)))
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
                                                 self.steps.latestCaliper['id'])
        return delete_Nones(self.initialqc_info)


class ProcessSpec():
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
            # 8) WORKSET            - get latest workset
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
        if aplication in ['Amplicon', 'Finished library']:
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
            if latest_caliper_id:
                library_validation["caliper_image"] = get_caliper_img(self.sample_name,
                                                            latest_caliper_id['id'])
            library_validations[agrlibQCstep['id']] = delete_Nones(library_validation)
        return delete_Nones(library_validations) 
