#!/usr/bin/env python

from datetime import date
from genologics.lims import *

def comp_dates(a, b):
    """Dates in isoformat. Is a < b?"""
    a = date(*map(int, a.split('-') ))
    b = date(*map(int, b.split('-') ))
    delta = a - b
    if delta.days < 0:
        return True
    else:
        return False

def delete_Nones(dict):
    "Deletes None type items from dict."
    new_dict = {}
    if dict:
        for key, val in dict.items():
            if val:
                if not val=='null':
                    if not (val=='2000-10-10' or val=='3000-10-10'):
                        new_dict[key] = val
    if new_dict != {}:
        return new_dict
    else:
        return None

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

def get_caliper_img(sample_name, caliper_id, lims):
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

