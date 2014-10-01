from setuptools import setup, find_packages
import sys
import os
import glob

setup(name = "scilifelab_parsers",
    version = "1.0",
    author = "Maya Brandi",
    author_email = "maya.brandi@scilifelab.se",
    description = "Feching data from LIMS and pushes into statusdb",
    py_modules = ['objectsDB'])
