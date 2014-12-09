from setuptools import setup, find_packages
import sys
import os
import glob

setup(name = "LIMS2DB",
    version = "1.0",
    author = "Maya Brandi",
    author_email = "maya.brandi@scilifelab.se",
    description = "Feching data from LIMS and pushes into statusdb",
    py_modules = ['LIMS2DB/objectsDB', 'scripts'],
    scripts = glob.glob('scripts/*.py'))
