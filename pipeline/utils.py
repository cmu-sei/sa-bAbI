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
"utils.py: data pipeline utilities for deep learning/vuln LENS"""
import json
import os
import pickle
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

# if user-specific constants exist, import them and override
try:
    import user_constants as constants
except ImportError:
    import constants

sys_path_parent = os.path.abspath('..')
if sys_path_parent not in sys.path:
    sys.path.append(sys_path_parent)
from sa_babi.sa_tag import Tag

# define names for the simple tokenization CSV
SIMP_TOK_NAMES = ['fname', 'kind', 'text', 'line', 'col', 'from_expansion']

# Juliet vulnerability-by-line manifest
JULIET_MANIFEST_PATH = '/srv/etc-str-01/project/dl-vuln/juliet1.3/src/C/manifest.xml'

# data paths
INSTANCE_FNAME = 'instances.npy'
LABEL_FNAME = 'labels.npy'
VOCAB_FNAME = 'vocab.pkl'
PARTITION_FNAME = 'partition.pkl'
PATHS_FNAME = 'paths.pkl'

# special tokens
LINE_FMT_STR = "<line %s>"
PAD_STR = "<bg>"
EMPTY_LINE_STR = "<empty>"
# I think this only occurs as the end-of-file token in the original
# simple tokenization
NAN_STR = "<nan>"


def generate_data(working_dir=constants.WORKING_DIR_JULIET_DATA):
    """Generate Juliet CWE121 data matrices and save in working dir

    Args:
        working_dir (str): path to dir to save data
    """
    print("Generating examples...")
    instances, labels, paths = get_examples(constants.ANNOTATED_TOK_DIR)
    vocab_mapping = get_vocab_mapping(instances)
    num_instances, max_numlines, max_linelen = get_data_dimensions(instances)
    instances_mat, labels_mat = get_example_matrices(instances, labels)
    partition = get_partition(num_instances)
    print("Done.")

    print_data_stats(instances, labels, vocab_mapping, partition, paths=paths)

    print("Saving data...")
    save_data(instances_mat, labels_mat, vocab_mapping, partition, paths,
              working_dir=working_dir)
    print("Done.")


def generate_choi_data(working_dir=constants.WORKING_DIR_CHOI_DATA):
    """Generate Choi data matrices and save in working dir

    Args:
        working_dir (str): path to dir to save data
    """
    print("Generating examples...")
    train_tok_file = os.path.join(constants.CHOI_TOK_DIR, 'training_100.tok')
    train_label_file = os.path.join(constants.CHOI_DATA_DIR,
                                    'training_100_labels.txt')
    train_instances, train_labels = get_choi_examples(train_tok_file,
                                                      train_label_file)

    test_tok_file = os.path.join(constants.CHOI_TOK_DIR, 'test_4_100.tok')
    test_label_file = os.path.join(constants.CHOI_DATA_DIR,
                                   'test_4_100_labels.txt')
    test_instances, test_labels = get_choi_examples(test_tok_file,
                                                    test_label_file)
    print("Done.")

    all_instances = train_instances + test_instances
    all_labels = train_labels + test_labels
    vocab_mapping = get_vocab_mapping(all_instances)
    instances_mat, labels_mat = get_example_matrices(all_instances, all_labels)

    # partition is deterministic, not random, because choi provide train/test
    # split
    num_train = len(train_instances)
    num_test = len(test_instances)
    partition = {
        'train': list(range(num_train)),
        'validation': list(range(num_train, num_train + num_test))
    }

    print_data_stats(all_instances, all_labels, vocab_mapping, partition)

    print("Saving data...")
    paths = None
    save_data(instances_mat, labels_mat, vocab_mapping, partition, paths,
              working_dir=working_dir)
    print("Done.")


def generate_sa_data(working_dir=constants.WORKING_DIR_SA_DATA,
                      coarse_labels=False):
    """Generate SA-bAbI data matrices and save in working dir

    Args:
        working_dir (str): path to dir to save data
        coarse_labels (bool): if True, then convert to just safe/unsafe
    """
    print("Generating examples...")
    instances, labels, paths = get_examples(constants.SA_TOK_DIR)

    # determine whether this is tautological-only
    unique_elements = set(lab for line in labels for lab in line)
    tautonly_elements = [
        itm.value for itm in
        [Tag.OTHER, Tag.BODY, Tag.BUFWRITE_TAUT_SAFE, Tag.BUFWRITE_TAUT_UNSAFE]]
    is_tautonly = unique_elements == set(tautonly_elements)

    if coarse_labels or is_tautonly:
        remapping = {4: 2, 5:3}
        labels = [[remapping[lab] if lab in remapping else lab
                   for lab in example] for example in labels]

    # Relabel "body" == "other" so they'll both be background/excluded
    # this will cause the labels in numpy matrices to disagree with
    # the metadata labels output from generate.py -metadata
    labels = [[max(lab - 1, 0) for lab in example] for example in labels]

    vocab_mapping = get_vocab_mapping(instances)
    num_instances, max_numlines, max_linelen = get_data_dimensions(instances)
    instances_mat, labels_mat = get_example_matrices(instances, labels)
    partition = get_partition(num_instances)
    print("Done.")

    print_data_stats(instances, labels, vocab_mapping, partition, paths=paths)

    print("Saving data...")
    save_data(instances_mat, labels_mat, vocab_mapping, partition, paths,
              working_dir=working_dir)
    print("Done.")


def print_data_stats(instances, labels, vocab_mapping, partition, paths=None):
    """Print data statistics to check"""
    num_instances, max_numlines, max_linelen = get_data_dimensions(instances)
    print("Stats:")
    print("\tNumber of examples: %s" % num_instances)
    print("\t\tTrain: %s\tTest: %s" %
          (len(partition['train']), len(partition['validation'])))
    print("\tMaximum number of lines (blanks removed): %s" % max_numlines)
    print("\tMaximum number of tokens per line: %s" % max_linelen)
    print("\tNumber of unique tokens: %s" % len(vocab_mapping))

    print("\nSpot check:")
    inst_idx = 0
    if paths is not None:
        print("Instance lines from %s and their labels:" % paths[inst_idx])
    else:
        print("Instance lines from inst %s and their labels:" % inst_idx)
    for idx in range(len(instances[inst_idx])):
        print("\t" + str(labels[inst_idx][idx]) +
              " " + str(instances[inst_idx][idx]))


def get_example_matrices(instances, labels):
    """Convert examples to 0-padded numpy arrays

    Args:
        instances (list): as returned from get_examples()
        labels (list): as returned from get_examples()

    Returns:
        instances_mat (np.ndarray) [num_examples, max_numlines, max_linelen]
        labels_mat (np.ndarray) [num_examples, max_numlines]
            labels_mat[i][j] is the i-th CWE121 C example, j-th line
                0 for "no label" if that example did not have max num lines
                1 if it is not labeled as CWE121,
                2 if it is labeled as CWE121
    """
    num_instances, max_numlines, max_linelen = get_data_dimensions(instances)
    vocab_mapping = get_vocab_mapping(instances)

    instances_mat = np.zeros((num_instances, max_numlines, max_linelen),
                             dtype='int32')
    labels_mat = np.zeros((num_instances, max_numlines), dtype='int32')

    # word mapping, with rank-3 padding
    for instance_idx, instance in enumerate(instances):
        for line_idx, line in enumerate(instance):
            for tok_idx, tok in enumerate(line):
                instances_mat[instance_idx][line_idx][
                    tok_idx] = vocab_mapping[tok]

            labels_mat[instance_idx][line_idx] = labels[instance_idx][line_idx]

    return instances_mat, labels_mat


def get_examples(tok_data_dir, test=False, num_examples=None,
                 use_annotated=True, add_line_num=True, juliet_labels=False):
    """Get all C examples of CWE121

    * strips the empty lines and reindexes labels accordingly

    Args:
        tok_data_dir (str): path to directory with token data files
        test (bool): if True, only get the first 5 examples
                     and suppress progress update
        num_examples (int): if None, get all examples
                            otherwise, get this many examples
        use_annotated (bool): if True, use annotated tokens
                              otherwise, use simple tokens
        add_line_num (bool): if True, then prepend line number
                             to each instance line
        juliet_labels (bool): if True, then get labels for Juliet, otherwise
                              get labels for SA-bAbI

    Returns:
        instances: list of list of list of str
            instances[i][j][k] represents
                - the i-th CWE121 C example
                - the j-th line
                - the k-th token in that line

        labels: list of list of int
            labels[i][j] represents
                - the i-th CWE121 C example
                - the j-th line

            in Juliet:
                the value is 1 if it is not labeled as CWE121, and 2 if it is

            in SA:
                the value is the integer Tag value

        paths: list of str, the token file used to generate each example
    """
    # get only C examples
    fname_suffix = ".c.tok" if use_annotated else ".c.simp"
    contents = sorted(os.listdir(tok_data_dir))
    if not contents:
        raise IOError("Empty token data dir: '%s'" % tok_data_dir)
    if os.path.isdir(os.path.join(tok_data_dir, contents[0])):
        path_list = [os.path.join(tok_data_dir, subdir, fname)
                     for subdir in contents
                     for fname in sorted(os.listdir(
                                         os.path.join(tok_data_dir, subdir)))
                     if fname.endswith(fname_suffix)]
    else:
        path_list = [os.path.join(tok_data_dir, fname)
                     for fname in contents
                     if fname.endswith(fname_suffix)]

    instances = []
    labels = []

    if test:
        num_examples = 5
    elif num_examples is None:
        num_examples = len(path_list)

    num_collected = 0
    paths = []

    vuln_lines_dict = None if not juliet_labels else get_vuln_lines()
    for file_idx, tok_path in enumerate(path_list):
        if num_examples is not None and num_collected >= num_examples:
            break

        if file_idx % 100 == 0 and not test:
            print("Processed %s/%s files" % (file_idx, num_examples))

        if use_annotated:
            lines, _ = ann_tok_to_lines(tok_path)
        else:
            lines = simp_tok_to_lines(tok_path)

        # get instance (code lines and tokens)
        this_instance = []
        for idx, line in enumerate(lines):
            # keep only nonempty lines
            if line:
                if add_line_num:
                    # add line number
                    line = [(LINE_FMT_STR % idx)] + line
                this_instance.append(line)

        instances.append(this_instance)

        # get labels
        c_filename = os.path.splitext(os.path.basename(tok_path))[0]

        if juliet_labels:
            this_label = get_juliet_label(vuln_lines_dict, c_filename, lines)
            labels.append(this_label)
        else:
            c_filepath = os.path.join(tok_data_dir, '..', 'src', c_filename)
            tags = get_sa_tags(c_filepath)
            # remove first tag--for `#include` line which is removed!
            tags = tags[1:]
            this_label = [tag.value for tag in tags]
            labels.append(this_label)

        num_collected += 1
        paths.append(tok_path)

    return instances, labels, paths


def get_juliet_label(vuln_lines_dict, c_filename, lines):
    """
    Args:
        vuln_lines_dict (dict)
        c_filename (str): filename to look up in juliet manifest
        lines (list of list of str)

    Returns:
        this_label (list of int):
            this_label[i] represents the i-th line
            the value is 1 if it is not labeled as CWE121, and 2 if it is
    """
    instance_vulns = vuln_lines_dict[c_filename]

    # filter for only CWE121
    vuln_lines = [line_num for (line_num, kind) in instance_vulns
                  if kind == 'CWE-121: Stack-based Buffer Overflow']

    this_label = []

    for idx, line in enumerate(lines):
        # keep only nonempty lines
        if line:
            label = 2 if idx in vuln_lines else 1
            this_label.append(label)

    return this_label


def get_choi_examples(tok_file, lab_file, replace_badchar=False):
    """Get Choi2017 dataset instances

    Args:
        tok_file (str): path to annotated Choi token JSON, e.g.
            /srv/etc-str-01/project/dl-vuln/choi_data/tokens/03_19_2018/*.tok
        lab_file (str): path to Choi dataset "csv", e.g.
            /srv/etc-str-01/project/dl-vuln/choi_data/test_1_100_labels.txt
        replace_badchar (bool): if True, then replace 0-byte character in
            training set ("'\\0'") with "'0'"

    Returns:
        instances: list of list of list of str
            instances[i][j][k] represents
                - the i-th function
                - the j-th line
                - the k-th token in that line

        labels: list of list of int
            labels[i][j] represents
                - the i-th function
                - the j-th line
            the value is:
                0 if it is not in the Choi labels
                1 if it is 1 in the Choi labels (safe)
                2 if it is 0 in the Choi labels (unsafe)
    """
    lines, funids = ann_tok_to_lines(tok_file)
    line_labels = pd.read_csv(lab_file, delimiter=':=:', engine='python',
                              names=['line', 'label'])
    line_labels = {line: label for (line, label) in
                   zip(line_labels['line'], line_labels['label'])}

    unique_funids = set(itm for funid_line in funids for itm in funid_line)
    instances = {funid: [] for funid in unique_funids}
    labels = {funid: [] for funid in unique_funids}
    for line_num, (line, funid_line) in enumerate(zip(lines, funids)):
        if funid_line == []:
            # empty line
            continue

        # can just get the first funId since each line is in exactly 1 func
        # in Choi2017 data specifically
        funid = funid_line[0]

        instances[funid].append(line)

        if line_num not in line_labels:
            labels[funid].append(0)
        elif line_labels[line_num] == 1:
            labels[funid].append(1)
        else:
            labels[funid].append(2)

    instances = [instances[idx] for idx in sorted(instances.keys())]
    labels = [labels[idx] for idx in sorted(labels.keys())]

    # prepend line numbers for each function
    numbered_instances = []
    for instance in instances:
        numbered_instance = []
        for idx, line in enumerate(instance):
            numbered_line = [LINE_FMT_STR % idx] + line
            numbered_instance.append(numbered_line)
        numbered_instances.append(numbered_instance)
    instances = numbered_instances

    if replace_badchar:
        instances = [
                     [["'0'" if tok == "'\\0'" else tok for tok in line]
                      for line in func]
                     for func in instances]

    return instances, labels


def save_data(instances_mat, labels_mat, vocab_mapping, partition, paths,
              working_dir=constants.WORKING_DIR):
    """Save matrices and vocab dict as .npy files

    Args:
        instances_mat (np.ndarray) returned from get_example_matrices()
        labels_mat (np.ndarray) returned from get_example_matrices()
        vocab_mapping (dict) returned from get_vocab_mapping()
        partition (dict) returned from get_partition
        paths (list of str) returned from get_examples()
        working_dir (str) path to dir to save .npy files
    """
    # numpy arrays
    for (arr, fname) in [
            (instances_mat, INSTANCE_FNAME),
            (labels_mat, LABEL_FNAME)]:
        np.save(os.path.join(working_dir, fname), arr)

    # dictionaries and lists
    pickle_list = [
        (vocab_mapping, VOCAB_FNAME),
        (partition, PARTITION_FNAME)]
    if paths is not None:
        pickle_list.append((paths, PATHS_FNAME))

    for (data_obj, fname) in pickle_list:
        with open(os.path.join(working_dir, fname), 'wb') as handle:
            pickle.dump(data_obj, handle)


def load_data(working_dir=constants.WORKING_DIR):
    """Load saved data matrices and vocab dict

    Args:
        working_dir (str): path to dir where .npy files are saved

    Returns:
        instances_mat (np.ndarray) as returned from get_example_matrices()
        labels_mat (np.ndarray) as returned from get_example_matrices()
        vocab_mapping (dict) as returned from get_vocab_mapping()
        partition (dict) as returned from get_partition()
        paths (list of str) as returned from get_examples(),
            or None if there was no path file
    """
    instances_mat = np.load(os.path.join(working_dir, INSTANCE_FNAME))
    labels_mat = np.load(os.path.join(working_dir, LABEL_FNAME))
    with open(os.path.join(working_dir, VOCAB_FNAME), 'rb') as handle:
        vocab_mapping = pickle.load(handle)
    with open(os.path.join(working_dir, PARTITION_FNAME), 'rb') as handle:
        partition = pickle.load(handle)

    paths = None
    pathfile_path = os.path.join(working_dir, PATHS_FNAME)
    if os.path.exists(pathfile_path):
        with open(pathfile_path, 'rb') as handle:
            paths = pickle.load(handle)

    return instances_mat, labels_mat, vocab_mapping, partition, paths


def get_label_counts(labels_mat):
    """Get dict of label counts

    Args:
        labels_mat (np.ndarray) as returned from get_example_matrices()

    Returns:
        label_counts (dict) maps label to number of occurrences
    """
    labels = list(np.unique(labels_mat))
    label_counts = {lab: (labels_mat == lab).sum() for lab in labels}
    return label_counts


def get_vocab_mapping(instances):
    """Get dict mapping vocab elements to integers

    Note: we reserve 0 for padding

    Args:
        instances (list): as returned from get_examples()

    Returns:
        vocab_mapping (dict)
    """
    vocab = [word for instance in instances
             for line in instance for word in line]
    vocab = sorted(list(set(vocab)))
    vocab_mapping = {word: idx + 1 for idx, word in enumerate(vocab)}
    return vocab_mapping


def get_data_dimensions(instances):
    """Get max number of lines and length of each line

    Args:
        instances (list): as returned from get_examples()

    Returns: tuple
        num_instances (int)
        max_numlines (int)
        max_linelen (int)
    """
    num_instances = len(instances)
    max_numlines = max(len(instance) for instance in instances)
    max_linelen = max(len(line) for instance in instances for line in instance)

    return num_instances, max_numlines, max_linelen


def simp_tok_to_lines(tok_file, include_header=False):
    """Convert simple token file (*.c.simp) to list of lines

    Args:
        tok_file (str): path to simple token file *.c.simp
        include_header (bool): if True, then include header lines

    Returns:
        lines (list of list of str)
    """
    tok_data = pd.read_csv(tok_file, names=SIMP_TOK_NAMES, header=None)
    if not include_header:
        tok_data = tok_data[tok_data['fname'].str.endswith(".c")]

    num_lines = max(tok_data['line'])
    line_data = {line_num: [] for line_num in range(num_lines + 1)}
    for _, row in tok_data.iterrows():
        text = row['text']
        if not isinstance(text, str):
            text = NAN_STR
        line_data[row['line']].append(text)

    lines = [line_data[key] for key in sorted(line_data.keys())]
    return lines


def ann_tok_to_lines(tok_file):
    """Convert annotated token file (*.c.tok) to list of lines
    and function IDs

    Args:
        tok_file (str): path to annotated token file
            e.g. dl-vuln/juliet1.3/tokens/cwe121_02_20_2018/
                           tokens/annotated/cwe121/s01/*.c.tok

    Returns:
        lines (list of list of str)
            lines[i][j] is the j-th token of the i-th line
        funids (list of list of int)
            funids[i][j] is the funId of the j-th token of the i-th line
    """
    with open(tok_file, 'rb') as handle:
        tok_data = json.load(handle)
    tok_data = tok_data['tokens']

    num_lines = max(itm['line'] for itm in tok_data)
    # num_lines + 1 because line numbers are 1-indexed, but we want to
    # 0-index. lines[0] will equal []
    line_data = {line_num: [] for line_num in range(num_lines + 1)}
    funids = {line_num: [] for line_num in range(num_lines + 1)}
    for itm in tok_data:
        text = itm['text']
        if not isinstance(text, str):
            raise ValueError('Token is not a string %s' % repr(text))
        line_data[itm['line']].append(text)

        if 'funId' in itm:
            funids[itm['line']].append(itm['funId'])

    lines = [line_data[key] for key in sorted(line_data.keys())]
    funids = [funids[key] for key in sorted(funids.keys())]
    return lines, funids


def get_vuln_lines():
    """Get a dict of all the Juliet vuln lines at once

    Returns:
        vuln_lines (dict)
            key (str): test case filename
            val (list of tuple): each elt is
                * line num (int)
                * CWE (str)
    """
    tree = ET.parse(JULIET_MANIFEST_PATH)
    root = tree.getroot()

    vuln_lines = dict()
    for testcase in root:
        for file_node in testcase:
            name = file_node.attrib['path']
            if name not in vuln_lines:
                vuln_lines[name] = []
            for flaw_node in file_node:
                attrs = flaw_node.attrib
                line_num = int(attrs['line'])
                cwe = attrs['name']
                vuln_lines[name].append((line_num, cwe))

    return vuln_lines


def get_partition(num_instances, train_frac=0.8):
    """Get dict of indices for train and validation split

    Inputs:
        num_instances (int): number of data instances
        train_frac (float): proportion of data to give to the training set

    Returns:
        partition (dict):
            'train': list of training set indices
            'validation': list of validation set indices
    """
    idx_arr = np.arange(num_instances)
    np.random.shuffle(idx_arr)
    idx_list = list(idx_arr)
    num_train = int(train_frac * num_instances)
    partition = {
        'train': idx_list[:num_train],
        'validation': idx_list[num_train:]
    }
    return partition


def get_tok_line(instance_line, vocab_mapping, as_str=True):
    """Get tokens for this instance line, for debug

    Args:
        instance_line (np.ndarray) [max_linelen,]
        vocab_mapping (dict): as returned by get_vocab_mapping
        as_str (bool): if True, return joined str representation
                       if False, return list of tokens

    Returns: list of str
    """
    if not isinstance(instance_line, np.ndarray):
        raise IOError("instance_line must be np.ndarray; got %s" %
                      type(instance_line))
    shape = instance_line.shape
    if not (len(shape) == 1 or
            (len(shape) == 2 and shape[0] == 1)):
        raise IOError("wrong shape; need [line_len,] or [1, line_len]; "
                      "got %s" % shape)

    if len(shape) == 2:
        instance_line = instance_line.flatten()

    inverse_vocab = {v: k for k, v in vocab_mapping.items()}
    # string to represent 0-padding
    line = [inverse_vocab[int(itm)]
            if int(itm) in inverse_vocab
            else PAD_STR
            for itm in instance_line]
    if as_str:
        line = " ".join(itm for itm in line if itm != PAD_STR)
        if not line:
            line = EMPTY_LINE_STR
    return line


def get_sa_tags(src_file):
    """Get list of SA-bAbI tags for this C source file
    Args:
        src_file (str): path to source file

    Returns:
        tags (list of Tag)
    """
    with open(src_file, 'r') as f:
        content = f.read()
    lines = content.split("\n")
    tag_strs = [itm.split("Tag.")[1] for itm in lines]
    tags = [Tag[itm] for itm in tag_strs]
    return tags


"""### TESTS #################################################"""


def _get_test_instances():
    instances, labels, paths = get_examples(constants.TEST_TOK_DIR, test=True)
    return instances, labels


def _test_get_examples(instances, labels):
    # the `#include` line is removed
    assert(instances[0][0] == ['<line 2>', 'int', 'main', '(', ')'])
    assert(instances[0][4] == ['<line 6>', 'char', 'entity_0', '[', '88', ']', ';'])
    assert(labels[0][17] == 2)


def _test_get_partition():
    num_instances = 10
    partition = get_partition(num_instances, train_frac=0.8)

    assert(isinstance(partition, dict))
    assert('train' in partition)
    assert(isinstance(partition['train'], list))
    assert(len(partition['train']) == 8)
    assert('validation' in partition)
    assert(isinstance(partition['validation'], list))
    assert(len(partition['validation']) == 2)
    assert(all(itm not in partition['validation']
               for itm in partition['train']))
    assert(all(itm not in partition['train']
               for itm in partition['validation']))


def _test_get_sa_tags():
    src_file = os.path.join(constants.TEST_SRC_DIR, '00000ed9c9.c')
    sa_tags = get_sa_tags(src_file)
    assert(len(sa_tags) == 26)
    assert(sa_tags[-8:] == [
            Tag.BUFWRITE_COND_SAFE,
            Tag.BODY,
            Tag.BODY,
            Tag.BODY,
            Tag.BUFWRITE_TAUT_UNSAFE,
            Tag.BUFWRITE_TAUT_SAFE,
            Tag.BODY,
            Tag.OTHER
        ])


def basic_examples_test():
    instances, labels, paths = get_examples(constants.TEST_TOK_DIR,
                                            test=True)

    # number of instances, number of labels
    assert(len(instances) == len(labels))
    # number of instances, number of paths
    assert(len(instances) == len(paths))
    # number of lines in first instance, number of labels for first instance
    assert(len(instances[0]) == len(labels[0]))


def _test():
    sa_data_available = (constants.SA_TOK_DIR is not None)

    if sa_data_available:
        # _test_get_sa_tags() # Need to find the proper seed to generate the test file / make a new one
        # basic_examples_test()
        # only get test instances once for speed
        # instances, labels = _get_test_instances()
        # _test_get_examples(instances, labels)
        1

    _test_get_partition()

_test()
