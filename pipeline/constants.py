# sa-bAbI: An automated software assurance code dataset generator
# 
# Copyright 2018 Carnegie Mellon University. All Rights Reserved.
#
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE
# ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS.
# CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER
# EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED
# TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY,
# OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON
# UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO
# FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
#
# Released under a MIT (SEI)-style license, please see license.txt or
# contact permission@sei.cmu.edu for full terms.
#
# [DISTRIBUTION STATEMENT A] This material has been approved for
# public release and unlimited distribution. Please see Copyright
# notice for non-US Government use and distribution.
# 
# Carnegie Mellon (R) and CERT (R) are registered in the U.S. Patent
# and Trademark Office by Carnegie Mellon University.
#
# This Software includes and/or makes use of the following Third-Party
# Software subject to its own license:
# 1. clang (http://llvm.org/docs/DeveloperPolicy.html#license)
#     Copyright 2018 University of Illinois at Urbana-Champaign.
# 2. frama-c (https://frama-c.com/download.html) Copyright 2018
#     frama-c team.
# 3. Docker (https://www.apache.org/licenses/LICENSE-2.0.html)
#     Copyright 2004 Apache Software Foundation.
# 4. cppcheck (http://cppcheck.sourceforge.net/) Copyright 2018
#     cppcheck team.
# 5. Python 3.6 (https://docs.python.org/3/license.html) Copyright
#     2018 Python Software Foundation.
# 
# DM18-0995
# 
"""constants.py: Constants for dl-vuln pipeline"""
# import os
from os import pardir, makedirs
from os.path import abspath, dirname, join, exists

# Find out where this file is
PIPELINE_DIR = dirname(abspath(__file__))
ROOT_DIR = abspath(join(PIPELINE_DIR, pardir ))


WORKING_DIR = join( ROOT_DIR,  'working')
WORKING_DIR_CHOI_DATA = None
WORKING_DIR_JULIET_DATA = None
# Specify training data here
WORKING_DIR_SA_DATA = join(WORKING_DIR, 'sa-train-1000/')

# Used in the arXiv paper
CHOI_DATA_DIR = None
CHOI_TOK_DIR = None
SIMPLE_TOK_DIR = None
ANNOTATED_TOK_DIR = None

SA_DATA_DIR = WORKING_DIR_SA_DATA
SA_SRC_DIR  = join(SA_DATA_DIR, 'src')
SA_TOK_DIR  = join(SA_DATA_DIR, 'tokens')

MODELS_DIR = join(WORKING_DIR_SA_DATA, 'models/')
if not exists(MODELS_DIR):
    makedirs(MODELS_DIR)

# This is for testing software, not testing a model
# TESTFILE_DIR = join(WORKING_DIR, 'sa-example-10/')
# TEST_SRC_DIR = join(TESTFILE_DIR, 'src')
# TEST_TOK_DIR = join(TESTFILE_DIR, 'tokens')
# TEST_WORKING_DIR = None

# Specify validation data here
VALIDATION_WORKING_PARENT_DIR = WORKING_DIR
VALIDATION_WORKING_SUBDIRS = [
    'sa-test-100',
]
VALIDATION_MODELS_PARENT_DIR = WORKING_DIR
VALIDATION_MODELS_SUBDIRS = [
    'sa-train-1000/models' # Note same as what was just trained for  this case.
]
VALIDATION_PREDICS_PARENT_DIR = WORKING_DIR
VALIDATION_PREDICS_SUBDIRS = [
    'sa-train-1000-predics',
]

VALIDATION_FIGURES_DIR = join(WORKING_DIR_SA_DATA, 'figures/')
if not exists(VALIDATION_FIGURES_DIR):
    makedirs(VALIDATION_FIGURES_DIR)

# Create plots for the paper
DO_CREATE_PLOTS = False
