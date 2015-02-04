from LIMS2DB.objectsDB.process_categories import *


"""Script to generate the process chategory info to a Read the Docs friendly rst
file. The script should be run from setup.py"""


GENERALINFO = """
What is a Process Category?
============================

In the project-statusdb context, lims processes are categorised into groups that define, or are used to define a certain type of status-db key in a project database. The categories are specified here. 


Adding a work flow.
==========================

If a work flow does not fit with the categories one might have to change the category definitions or ad new categories. This needs to be done in corperation with the developer of project_summary_uppload_LIMS.py. The cathegories are defined in process_categories.py within the objectsDB package.
"""
SECTIONSTART = "==============================="
SECTIONMIDLE = """

=== =======================================
ID  process Name
=== ======================================="""
SECTIONEND = """=== =======================================
    
"""

def make_doc():
    f = open('docs/process_categories.rst', 'w')
    print >> f, GENERALINFO
    for cat in PROCESSCATEGORIES:
        print >> f, cat
        print >> f, SECTIONSTART
        print >> f, PROCESSCATEGORIES[cat]['Description']
        print >> f, SECTIONMIDLE
        for id, name in PROCESSCATEGORIES[cat].items():
            if not id=='Description':
                print >> f, '\t'.join([id, name])
        print >> f, SECTIONEND
    f.close()

