#!/usr/bin/env python
"""Script to load project info from Lims into the project database in statusdb.

Maya Brandi, Science for Life Laboratory, Stockholm, Sweden.
"""
#from __future__ import print_function
#import sys
#import os
#import codecs
#from optparse import OptionParser
#from statusdb.db.utils import *
#from pprint import pprint
#from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD

#import LIMS2DB.objectsDB.objectsDB as DB
#from LIMS2DB.objectsDB.functions import *

#import datetime
#import time
#import multiprocessing as mp
#import Queue
#import logging
#import logging.handlers

   
class PSUL():
    def __init__(self, proj, samp_db, proj_db, upload_data, days, man_name, output_f, log):
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
        self.lims = Lims(BASEURI, USERNAME, PASSWORD)
        self.log=log

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
            self.log.info("Project is not updated because 'Order received' date and "
                     "'open date' is missing for project {name}".format(
                     name = self.name))

    def get_days_closed(self):
        """Project registered as closed?"""

        if self.close_date:
            closed=datetime.datetime.strptime(self.close_date,"%Y-%m-%d" )
            return (datetime.datetime.today() - closed).days
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
        #try:
        if 1==1:
            self.log.info('Handeling {proj}'.format(proj = self.name))
            project = database.ProjectDB(self.lims, self.id, self.samp_db)
            key = find_proj_from_view(self.proj_db, self.name)
            project.obj['_id'] = find_or_make_key(key)
#            if not opended_after_140630:
#                try:
#                    project.obj = load_status_from_google_docs.get(self.name, project.obj)
#                except RequestError:
#                    return "Failed to get the 20158 spreadsheet for project{}".format(self.id)
            if self.upload_data:
                info = save_couchdb_obj(self.proj_db, project.obj)
            else:
                info = self.print_couchdb_obj_to_file(project.obj)
            return "project {name} is handled and {info}: _id = {id}".format(
                               name=self.name, info=info, id=project.obj['_id'])
#        except:
#            return ('Issues geting info for {name}. The "Application" udf might'
#                                         ' be missing'.format(name = self.name))

    def project_update_and_logging(self):
        start_time = time.time()
        self.get_ordered_opened()
        if self.ordered_opened:
            log_info = self.determine_update()
        else:
            log_info = ('No open date or order date found for project {name}. '
                        'Project not updated.'.format(name = self.name))
        elapsed = time.time() - start_time
        self.log.info('Time - {elapsed} : Proj Name - '
                 '{name}'.format(elapsed = elapsed, name = self.name))
        self.log.info(log_info) 

def main(options):
    man_name = options.project_name
    all_projects = options.all_projects
    days = options.days
    conf = options.conf
    upload_data = options.upload
    output_f = options.output_f
    couch = load_couch_server(conf)
    proj_db = couch['projects']
    samp_db = couch['samples']
    mainlims = Lims(BASEURI, USERNAME, PASSWORD)
    mainlog = logging.getLogger('psullogger')
    mainlog.setLevel(level=logging.INFO)
    mfh = logging.FileHandler(options.logfile)
    mft = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    mfh.setFormatter(mft)
    mainlog.addHandler(mfh)

    if all_projects:
        projects = mainlims.get_projects()
        masterProcess(options,projects, mainlims, mainlog)
    elif man_name:
        proj = mainlims.get_projects(name = man_name)
        if not proj:
            mainlog.warn('No project named {man_name} in Lims'.format(
                        man_name = man_name))
        else:
            P = PSUL(proj[0], samp_db, proj_db, upload_data, days, man_name, output_f, mainlog)
            P.project_update_and_logging()

def processPSUL(options, queue, logqueue):
    couch = load_couch_server(options.conf)
    proj_db = couch['projects']
    samp_db = couch['samples']
    mylims = Lims(BASEURI, USERNAME, PASSWORD)
    work=True
    procName=mp.current_process().name
    proclog=logging.getLogger(procName)
    proclog.setLevel(level=logging.INFO)
    mfh = QueueHandler(logqueue)
    mft = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    mfh.setFormatter(mft)
    proclog.addHandler(mfh)

    while work:
        #grabs project from queue
        try:
            projname = queue.get(block=True, timeout=3)
        except Queue.Empty:
            work=False
            proclog.info("exiting gracefully")
            break
        else:
            proj=mylims.get_projects(name=projname)[0]
            P = PSUL(proj, samp_db, proj_db, options.upload, options.days, options.project_name, options.output_f, proclog)
            P.project_update_and_logging()
            #signals to queue job is done
            queue.task_done()

def masterProcess(options,projectList, mainlims, logger):
    projectsQueue=mp.JoinableQueue()
    logQueue=mp.Queue()
    childs=[]
    #Initial step : order projects by sample number:
    logger.info("ordering the project list")
    orderedprojectlist=sorted(projectList, key=lambda x: (mainlims.get_sample_number(projectname=x.name)), reverse=True)
    logger.info("done ordering the project list")
    #spawn a pool of processes, and pass them queue instance 
    for i in range(options.processes):
        p = mp.Process(target=processPSUL, args=(options,projectsQueue, logQueue))
        p.start()
        childs.append(p)
    #populate queue with data   
    for proj in orderedprojectlist:
        projectsQueue.put(proj.name)

    #wait on the queue until everything has been processed     
    notDone=True
    while notDone:
        try:
            log=logQueue.get(False)
            logger.handle(log)
        except Queue.Empty:
            if not stillRunning(childs):
                notDone=False
                break

def stillRunning(processList):
    ret=False
    for p in processList:
        if p.is_alive():
            ret=True

    return ret

class QueueHandler(logging.Handler):
    """
    This handler sends events to a queue. Typically, it would be used together
    with a multiprocessing Queue to centralise logging to file in one process
    (in a multi-process application), so as to avoid file write contention
    between processes.

    This code is new in Python 3.2, but this class can be copy pasted into
    user code for use with earlier Python versions.
    """

    def __init__(self, queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue

    def enqueue(self, record):
        """
        Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method if you want to use blocking, timeouts or custom queue
        implementations.
        """
        self.queue.put_nowait(record)

    def prepare(self, record):
        """
        Prepares a record for queuing. The object returned by this method is
        enqueued.

        The base implementation formats the record to merge the message
        and arguments, and removes unpickleable items from the record
        in-place.

        You might want to override this method if you want to convert
        the record to a dict or JSON string, or send a modified copy
        of the record while leaving the original intact.
        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue, preparing it for pickling first.
        """
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            self.handleError(record)
                  
if __name__ == '__main__':
    usage = "Usage:       python project_summary_upload_LIMS.py [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--project", dest = "project_name", default = None,
                      help = "eg: M.Uhlen_13_01. Dont use with -a flagg.")
    parser.add_option("-a", "--all_projects", dest = "all_projects", action = 
                      "store_true", default = False, help = ("Upload all Lims ",
                      "projects into couchDB. Don't use with -f flagg."))
    parser.add_option("-d", "--days",type='int', dest = "days", default = 60, help = (
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
    parser.add_option("-m", "--multiprocs", type='int', dest = "processes", default = 4,
                      help = "How many processes will be spawned. Will only work with -a")
    parser.add_option("-l", "--logfile", dest = "logfile", help = ("log file",
                      " that will be used. default is $HOME/lims2db_projects.log "), default=os.path.expanduser("~/lims2db_projects.log"))

    (options, args) = parser.parse_args()
    main(options)

