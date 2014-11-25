#!/usr/bin/env python
from __future__ import print_function
"""Script to load project info from Lims into the project database in statusdb.

Maya Brandi, Science for Life Laboratory, Stockholm, Sweden.
"""

import sys
import os
import codecs
from optparse import OptionParser
import load_status_from_google_docs 
from scilifelab.db.statusDB_utils import *
from helpers import *
from pprint import pprint
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
import objectsDB as DB
from datetime import date
import time
import scilifelab.log
import threading
import Queue 
lims = Lims(BASEURI, USERNAME, PASSWORD)
LOG = scilifelab.log.minimal_logger('LOG')
projectsQueue=Queue.Queue()
   
class PSUL():
    def __init__(self, proj, samp_db, proj_db, upload_data, days, man_name, output_f):
        self.proj = proj
        self.id = proj.id
        self.udfs = proj.udf
        self.name = proj.name
        self.open_date = proj.open_date
        self.close_date = proj.close_date
        self.samp_db = samp_db
        self.proj_db = proj_db
        self.upload_data = upload_data
        self.man_name = man_name
        self.days = days
        self.output_f = output_f
        self.ordered_opened = None

    def print_couchdb_obj_to_file(self, obj):
        if self.output_f is not None:
            with open(self.output_f, 'w') as f:
                print(obj, file = f)
        else:
            print(obj, file = sys.stdout)

    def get_ordered_opened(self):
        """Is project registered as opened or ordered?"""

        if self.open_date:
            self.ordered_opened = self.open_date
        elif 'Order received' in dict(self.udfs.items()).keys():
            self.ordered_opened = self.udfs['Order received'].isoformat()
        else:
            LOG.info("Project is not updated because 'Order received' date and "
                     "'open date' is missing for project {name}".format(
                     name = self.name))

    def get_days_closed(self):
        """Project registered as closed?"""

        if self.close_date:
            closed = date(*map(int, self.close_date.split('-')))
            return (date.today() - closed).days
        else:
            return 0

    def determine_update(self):
        """Determine wether to and how to update project"""
        days_closed = self.get_days_closed()
        opended_after_130630 = comp_dates('2013-06-30', self.ordered_opened)
        closed_for_a_while = (days_closed > self.days)
        log_info = ''
        if (not opended_after_130630) or closed_for_a_while:
            if self.man_name:   ## Ask wether to update
                start_update = raw_input("""
                Project {name} was ordered or opended at {ord_op} and has been 
                closed for {days} days. Do you still want to load the data from 
                lims into statusdb? 
                Press enter for No, any other key for Yes! """.format(
                name = self.name, ord_op = self.ordered_opened, days = days_closed))
            else:               ## Do not update
                start_update = False
                log_info = ('Project is not updated because: ')
                if closed_for_a_while:
                    log_info += ('It has been closed for {days} days. '.format(
                                 days = days_closed))
                if not opended_after_130630:
                    log_info += ('It was opened or ordered before 2013-06-30 '
                                 '({ord_op})'.format(ord_op = self.ordered_opened))
        else:
            start_update = True

        if start_update:
            log_info = self.update_project(DB)
        return log_info

    def update_project(self, database):
        """Fetch project info and update project in the database."""
        opended_after_140630 = comp_dates('2014-06-30', self.ordered_opened)
        try:
            LOG.info('Handeling {proj}'.format(proj = self.name))
            project = database.ProjectDB(lims, self.id, self.samp_db)
            key = find_proj_from_view(self.proj_db, self.name)
            project.obj['_id'] = find_or_make_key(key)
            if not opended_after_140630:
                project.obj = load_status_from_google_docs.get(self.name, project.obj)
            if self.upload_data:
                info = save_couchdb_obj(self.proj_db, project.obj)
            else:
                info = self.print_couchdb_obj_to_file(project.obj)
            return "project {name} is handled and {info}: _id = {id}".format(
                               name=self.name, info=info, id=project.obj['_id'])
        except:
            return ('Issues geting info for {name}. The "Application" udf might'
                                         ' be missing'.format(name = self.name))

    def project_update_and_logging(self):
        start_time = time.time()
        self.get_ordered_opened()
        if self.ordered_opened:
            log_info = self.determine_update()
        else:
            log_info = ('No open date or order date found for project {name}. '
                        'Project not updated.'.format(name = self.name))
        elapsed = time.time() - start_time
        LOG.info('Time - {elapsed} : Proj Name - '
                 '{name}'.format(elapsed = elapsed, name = self.name))
        LOG.info(log_info) 

def main(options):
    man_name=options.project_name
    all_projects=options.all_projects
    days=options.days
    conf=options.conf
    upload_data=options.upload
    output_f = options.output_f
    couch = load_couch_server(conf)
    proj_db = couch['projects']
    samp_db = couch['samples']

    if all_projects:
        projects = lims.get_projects()
        masterThread(options,projects)
    elif man_name:
        proj = lims.get_projects(name = man_name)
        if not proj:
            LOG.warning('No project named {man_name} in Lims'.format(
                        man_name = man_name))
        else:
            P = PSUL(proj[0], samp_db, proj_db, upload_data, days, man_name, output_f)
            P.project_update_and_logging()

class ThreadPSUL(threading.Thread):
    def __init__(self, options,queue):
        threading.Thread.__init__(self)
        self.options=options
        self.queue = queue
        couch = load_couch_server(options.conf)
        self.proj_db = couch['projects']
        self.samp_db = couch['samples']
    def run(self):
        while True:
            #grabs project from queue
            proj = self.queue.get(block=True, timeout=2)
            P = PSUL(proj, self.samp_db, self.proj_db, self.options.upload, self.options.days, self.options.project_name, self.options.output_f)
            P.project_update_and_logging()
            #signals to queue job is done
            self.queue.task_done()
            if self.queue.empty()  :
                break


def masterThread(options,projectList):
#spawn a pool of threads, and pass them queue instance 
    for i in range(options.threads):
        t = ThreadPSUL(options,projectsQueue)
        t.start()
#populate queue with data   
    for proj in projectList:
        projectsQueue.put(proj)

#wait on the queue until everything has been processed     
    projectsQueue.join()
                  

if __name__ == '__main__':
    usage = "Usage:       python project_summary_upload_LIMS.py [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--project", dest = "project_name", default = None,
                      help = "eg: M.Uhlen_13_01. Dont use with -a flagg.")
    parser.add_option("-a", "--all_projects", dest = "all_projects", action = 
                      "store_true", default = False, help = ("Upload all Lims ",
                      "projects into couchDB. Don't use with -f flagg."))
    parser.add_option("-d", "--days", dest = "days", default = 60, help = (
                      "Projects with a close_date older than DAYS days are not",
                      " updated. Default is 60 days. Use with -a flagg"))
    parser.add_option("-c", "--conf", dest = "conf", default = os.path.join(
                      os.environ['HOME'],'opt/config/post_process.yaml'), help =
                      "Config file.  Default: ~/opt/config/post_process.yaml")
    parser.add_option("--no_upload", dest = "upload", default = True, action = 
                      "store_false", help = ("Use this tag if project objects ",
                      "should not be uploaded, but printed to output_f, or to ",
                      "stdout"))
    parser.add_option("--output_f", dest = "output_f", help = ("Output file",
                      " that will be used only if --no_upload tag is used"), default=None)
    parser.add_option("-t", "--threads", type='int', dest = "threads", default = 4,
                      help = "How many threads will be spawned. Will only work with -a")

    (options, args) = parser.parse_args()
    LOG = scilifelab.log.file_logger('LOG', options.conf, 'lims2db_projects.log'
                                                               ,'log_dir_tools')
 
    main(options)

