#!/home/maya.brandi/anaconda/envs/LIMS2DB150125/bin/python
import sys
import os
import time
from  datetime  import  datetime
from uuid import uuid4
import hashlib
from optparse import OptionParser
import logging
import bcbio.pipeline.config_utils as cl
from scilifelab.google.google_docs import SpreadSheet
from scilifelab.google import get_credentials
import couchdb
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
from statusdb.db.utils import *
lims = Lims(BASEURI, USERNAME, PASSWORD)

#           GOOGLE DOCS
def get_google_document(ssheet_title, wsheet_title, client):
    ssheet = client.get_spreadsheet(ssheet_title)
    wsheet = client.get_worksheet(wsheet_title)
    content = client.get_cell_content(wsheet)
    ss_key = client.get_key(ssheet)
    ws_key = client.get_key(wsheet)
    return content, ws_key, ss_key

def get_column(ssheet_content, header, col_cond=0):
    colindex=''
    for j, row in enumerate(ssheet_content):
        if colindex == '':
            for i, col in enumerate(row):
                if col_cond <= i and colindex == '':
                    if str(col).strip().replace('\n','').replace(' ','') == header.replace(' ',''):
                        colindex = i
        else:
            rowindex = j-1
            return rowindex, colindex

# NAME STRIP
def strip_index(name):
    indexes = ['_nxdual','_index','_rpi','_agilent','_mondrian','_haloht',
        '_halo','_sureselect','_dual','_hht','_ss','_i','_r','_a','_m','_h']
    name = name.replace('-', '_').replace(' ', '')
    for i in indexes:
        name=name.split(i)[0]
    preps='FBCDEF'
    for prep in preps:
        name=name.rstrip(prep)
    return name

def get_20158_info(credentials, project_name_swe):
    versions = {"01": ['Sample name Scilife', "Total reads per sample", "Sheet1","Passed=P/ not passed=NP*"],
            "02": ["Sample name (SciLifeLab)", "Total number of reads (Millions)","Sheet1",
              "Based on total number of reads after mapping and duplicate removal"],
            "03": ["Sample name (SciLifeLab)", "Total number of reads (Millions)","Sheet1",
              "Based on total number of reads after mapping and duplicate removal "],
            "05": ["Sample name (from Project read counts)", "Total number","Sheet1",
              "Based on total number of reads","Based on total number of reads after mapping and duplicate removal"],
            "06": ["Sample name (from Project read counts)", "Total number","Sheet1",
              "Based on total number of reads","Based on total number of reads after mapping and duplicate removal"]}
    info = {}
    client = SpreadSheet(credentials)
    feed = client.get_spreadsheets_feed(project_name_swe + '_20158', False)
    if len(feed.entry) != 0:
        ssheet = feed.entry[0].title.text
        version = ssheet.split(str('_20158_'))[1].split(' ')[0].split('_')[0]
        client = SpreadSheet(credentials, ssheet) 
        content, ws_key, ss_key = get_google_document(ssheet,  versions[version][2], client)
        dummy, P_NP_colindex = get_column(content, versions[version][3])
        dummy, No_reads_sequenced_colindex = get_column(content, versions[version][1])
        row_ind, scilife_names_colindex = get_column(content, versions[version][0])
        if (version=="05")| (version=="06"):
            dummy, P_NP_duprem_colindex = get_column(content, versions[version][4]) ## [version][4] for dup rem
        else:
            P_NP_duprem_colindex=''
        for j, row in enumerate(content):
            if (j > row_ind):
                try:
                    sci_name = str(row[scilife_names_colindex]).strip()
                    striped_name = strip_index(sci_name)
                    no_reads = str(row[No_reads_sequenced_colindex]).strip()
                    if (P_NP_duprem_colindex!='') and (str(row[P_NP_duprem_colindex]).strip()!=''):
                        status = str(row[P_NP_duprem_colindex]).strip()
                    else:
                        status = str(row[P_NP_colindex]).strip()
                    info[striped_name] = [status,no_reads]
                except:
                    pass
    else:
        info=None
    return info

def set_db_fields(info, proj):
    if info:
        if proj.has_key('samples'):
            for sample in proj['samples']:
                if sample in info.keys():
                    proj['samples'][sample]['status'] = info[sample][0]
                    proj['samples'][sample]['m_reads_sequenced'] = info[sample][1]
                    if not proj['samples'][sample].has_key('details'):
                        proj['samples'][sample]['details'] = {
                                            'status_(manual)' : info[sample][1],
                                            'total_reads_(m)' : info[sample][0]}
                    else:
                        if not proj['samples'][sample]['details'].has_key('status_(manual)'):
                            proj['samples'][sample]['details']['status_(manual)'] = info[sample][1]
                        if not proj['samples'][sample]['details'].has_key('total_reads_(m)'):
                            proj['samples'][sample]['details']['total_reads_(m)'] = info[sample][0]
    return proj

def main(project_name, conf):
    couch = load_couch_server(conf)
    proj_db = couch['projects']
    key = find_proj_from_view(proj_db, project_name)
    print key
    proj = proj_db.get(key)
    if not proj:
        LOG.warning('No project named {man_name} in Lims'.format(
                        man_name = project_name))
    else:
        CREDENTIALS_FILE = os.path.join(os.environ['HOME'], 'opt/config/gdocs_credentials')
        credentials = get_credentials(CREDENTIALS_FILE)
        info = get_20158_info(credentials, project_name)
        proj = set_db_fields(info, proj)
        save_couchdb_obj(proj_db, proj)

if __name__ == '__main__':
    usage = "Usage:     load_status_from_google_docs.py [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--project", dest = "project_name", default = None,
                      help = "eg: M.Uhlen_13_01. Dont use with -a flagg.")
    parser.add_option("-c", "--conf", dest = "conf", default = os.path.join(
                      os.environ['HOME'],'opt/config/post_process.yaml'), help =
                      "Config file.  Default: ~/opt/config/post_process.yaml")

    (options, args) = parser.parse_args()
    main(options.project_name, options.all_projects, options.conf)

