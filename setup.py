from setuptools import setup, find_packages
import sys
import os
import glob

try:
    with open("requirements.txt", "r") as f:
        install_requires = [x.strip() for x in f.readlines()]
except IOError:
    install_requires = []

setup(name = "LIMS2DB",
    version = "1.0",
    author = "Maya Brandi",
    author_email = "maya.brandi@scilifelab.se",
    description = "Feching data from LIMS and pushes into statusdb",
    packages=find_packages(),
    scripts = glob.glob('scripts/*.py'))


from LIMS2DB.objectsDB import make_process_category_doc
make_process_category_doc.make_doc()

