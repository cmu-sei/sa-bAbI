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
"""subset.py: get subset of large dataset"""

import os

import numpy as np

import utils


def make_subset(train_size, outdir,
                working_dir=utils.constants.WORKING_DIR_SA_DATA):
    """Get subset of large dataset and save

    Args:
        train_size (int)
        outdir (path): where to save subset
        working_dir (str): working dir that large dataset npy files are in
    """
    inst, lab, voc, part, paths = utils.load_data(working_dir)

    orig_train_idx = part['train']
    val_idx = part['validation']

    train_idx = orig_train_idx[:train_size]

    inst = np.concatenate((inst[train_idx], inst[val_idx]))
    lab = np.concatenate((lab[train_idx], lab[val_idx]))
    num_examples = inst.shape[0]
    part = {
        'train': list(range(train_size)),
        'validation': list(range(train_size, num_examples))
    }
    paths = ([paths[idx] for idx in train_idx] +
             [paths[idx] for idx in val_idx])

    utils.save_data(inst, lab, voc, part, paths, outdir)


def main():
    parent = '/Users/cdsestili/Documents/dl-vuln/data/working/sa_data/'
    for (size, subdir) in [
        (9600, '9600_train_data'),
        (19200, '19200_train_data'),
        (38400, '38400_train_data'),
        (76800, '76800_train_data')]:
        outdir = os.path.join(parent, subdir)
        make_subset(size, outdir)
