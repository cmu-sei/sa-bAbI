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
"""validate.py: validate memory network models"""

import os

import keras.models
import matplotlib.pyplot as plt
import numpy as np
import sklearn.metrics

# if user-specific constants exist, import them and override
try:
    import user_constants as constants
except ImportError:
    import constants
import datagen
import juliet_memnet
import utils

NUM_MODELS_PER_EXPERIMENT = 10
NUM_EXPER = len(constants.VALIDATION_MODELS_SUBDIRS)

MODEL_FNAMES = ['model_{}.h5'.format(model_num)
                for model_num in range(NUM_MODELS_PER_EXPERIMENT)]

# metrics for code-analysis tools
# tool name, full subset, sound subset
TOOL_ACCURACIES = [
    ('comm.\ntool', 0.923, 0.910),
    ('clang_sa', 0.749, 0.842),
    ('frama-c', 0.848, 0.983),
    ('cppcheck', 0.803, 0.769)
]
TOOL_PRECISIONS = [
    ('comm.\ntool', 1, 1),
    ('clang_sa', 0.999, 0.999),
    ('frama-c', 1, 1),
    ('cppcheck', 0.967, 0.959)
]
TOOL_RECALLS = [
    ('comm.\ntool', 0.868, 0.850),
    ('clang_sa', 0.573, 0.739),
    ('frama-c', 0.742, 0.972),
    ('cppcheck', 0.688, 0.642)
]
TOOL_F1S = [
    ('comm.\ntool', 0.930, 0.919),
    ('clang_sa', 0.729, 0.849),
    ('frama-c', 0.852, 0.986),
    ('cppcheck', 0.804, 0.769)
]

TRAIN_SET_SIZES = ['9600', '19200', '38400', '76800', '153600']


def analyze_train_set_size(do_print_confusions=False):

    for use_sound_subset in [False, True]:

        accuracies = np.zeros((NUM_MODELS_PER_EXPERIMENT, NUM_EXPER))
        precisions = np.zeros((NUM_MODELS_PER_EXPERIMENT, NUM_EXPER))
        recalls = np.zeros((NUM_MODELS_PER_EXPERIMENT, NUM_EXPER))
        f1s = np.zeros((NUM_MODELS_PER_EXPERIMENT, NUM_EXPER))

        for (exper_num, (working_subdir, model_subdir, predics_subdir)
             ) in enumerate(zip(
                constants.VALIDATION_WORKING_SUBDIRS,
                constants.VALIDATION_MODELS_SUBDIRS,
                constants.VALIDATION_PREDICS_SUBDIRS)):

            working_dir = os.path.join(constants.VALIDATION_WORKING_PARENT_DIR,
                                       working_subdir)
            models_dir = os.path.join(constants.VALIDATION_MODELS_PARENT_DIR,
                                      model_subdir)

            (val_instances_mat, val_queries_mat, y_true
             ) = get_val_data(working_dir, get_sound=use_sound_subset)

            y_true = map_to_coarse(y_true)

            # get predictions for each model
            separate_predics = get_separate_predics(
                predics_subdir, models_dir, val_instances_mat, val_queries_mat,
                use_sound_subset)

            if do_print_confusions:
                print_confusions(y_true, separate_predics)

            # assemble metrics
            for model_num in range(NUM_MODELS_PER_EXPERIMENT):
                print(model_num)
                y_pred = separate_predics[model_num]
                accuracies[model_num, exper_num] = (
                    sklearn.metrics.accuracy_score(y_true, y_pred))
                precisions[model_num, exper_num] = (
                    sklearn.metrics.precision_score(y_true, y_pred))
                recalls[model_num, exper_num] = (
                    sklearn.metrics.recall_score(y_true, y_pred))
                f1s[model_num, exper_num] = sklearn.metrics.f1_score(
                    y_true, y_pred)

        if constants.DO_CREATE_PLOTS:
            create_plots(accuracies, precisions, recalls, f1s, use_sound_subset)



def get_separate_predics(predics_subdir, models_dir, val_instances_mat,
                         val_queries_mat, use_sound_subset):
    # only load models if necessary
    models = None
    separate_predics = []
    for predic_num in range(NUM_MODELS_PER_EXPERIMENT):
        fname = 'predics_{}.npy'.format(predic_num)
        if use_sound_subset:
            subdir = 'sound_val_set'
        else:
            subdir = 'full_val_set'
        path = os.path.join(constants.VALIDATION_PREDICS_PARENT_DIR,
                            subdir, predics_subdir, fname)
        if not os.path.exists(path):
            if models is None:
                models = get_models(models_dir)
            predic = models[predic_num].predict(
                [val_instances_mat, val_queries_mat])
            print(path)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            np.save(path, predic)
        else:
            predic = np.load(path)
        separate_predics.append(predic)

    # convert to labels for confusion
    separate_predics = [np.argmax(y_pred, axis=1) for y_pred in
                        separate_predics]
    separate_predics = [map_to_coarse(y_pred) for y_pred in separate_predics]

    return separate_predics


def get_models(models_dir):
    print("loading models from '%s'" % models_dir)
    custom_objects = {'PositionEncode': juliet_memnet.PositionEncode}
    models = []
    for fname in MODEL_FNAMES:
        path = os.path.join(models_dir, fname)
        if not os.path.exists(path):
            print("Warning: could not find model file '%s'" % path)
            continue
        model = keras.models.load_model(path, custom_objects=custom_objects)
        models.append(model)

    return models


def get_val_data(working_dir, get_sound=False):
    print("loading validation data from '%s'" % working_dir)
    _, _, _, partition, _ = utils.load_data(working_dir=working_dir)
    validation_ids = partition['validation']
    total_num_samples = len(validation_ids)
    print("Number of val instances: %s" % total_num_samples)

    val_data_generator = datagen.DataGenerator(working_dir=working_dir)

    if get_sound:
        (val_instances_mat, val_queries_mat), val_labels_mat = (
            val_data_generator.get_sound_samples(validation_ids)
        )
    else:
        (val_instances_mat, val_queries_mat), val_labels_mat = (
            val_data_generator.get_samples(validation_ids)
        )

    y_true = np.argmax(val_labels_mat, axis=1)

    print("Label counts:")
    labels, counts = np.unique(y_true, return_counts=True)
    print(labels)
    print(counts)
    total_num_queries = sum(counts)
    print("total: %s" % total_num_queries)
    queries_per_sample = total_num_queries / total_num_samples
    print("Average queries per sample: %s" % queries_per_sample)

    return val_instances_mat, val_queries_mat, y_true


def print_confusions(y_true, separate_predics):
    print("confusion matrices:")
    for predic in separate_predics:
        cnf_matrix = sklearn.metrics.confusion_matrix(y_true, predic)
        print(cnf_matrix)
        print()


def get_ensemble_scores(separate_scores):
    # soft voting. we're probably not going to use this for the analysis
    ens_scores = np.mean(separate_scores, axis=0)
    return ens_scores


def map_to_coarse(labels):
    # safe to 0, unsafe to 1
    mapping = {0: 0, 1: 1, 2: 0, 3: 1}
    labels = np.vectorize(mapping.get)(labels)
    return labels


def create_plots(accuracies, precisions, recalls, f1s, use_sound_subset,
                 verbose=True):
    # key: (plot title, metrics array, tool metric list)
    metric_data = {
        'accuracy': ('Accuracy', accuracies, TOOL_ACCURACIES),
        'precision': ('Precision', precisions, TOOL_PRECISIONS),
        'recall': ('Recall', recalls, TOOL_RECALLS),
        'f1': ('F1', f1s, TOOL_F1S)
    }

    for key, (name, metric_results, tool_metrics) in metric_data.items():

        if verbose:
            print(name)
            print(metric_results)
            print("min:")
            print(np.min(metric_results, axis=0))
            print("median:")
            print(np.median(metric_results, axis=0))
            print("max:")
            print(np.max(metric_results, axis=0))

        plt.gcf().clear()
        suffix = " (sound)" if use_sound_subset else " full)"
        title = name + suffix
        plt.title(title)
        plt.boxplot(metric_results)
        # horizontal lines for tools
        for tool_name, full_metric, sound_metric in tool_metrics:
            line_x_start = 0.5
            line_x_end = NUM_EXPER + 0.5

            plot_value = sound_metric if use_sound_subset else full_metric

            plt.hlines(plot_value, line_x_start, line_x_end)
            plt.text(line_x_end, plot_value, tool_name)
            plt.xticks(np.arange(NUM_EXPER) + 1, TRAIN_SET_SIZES)
            plt.xlabel('Training set size (number of files)')
        fname = '{}.pdf'.format(key)
        if use_sound_subset:
            subdir = 'sound_val_set'
        else:
            subdir = 'full_val_set'
        path = os.path.join(constants.VALIDATION_FIGURES_DIR, subdir, fname)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        plt.savefig(path)


def evaluate_oneoff(working_dir, models_dir, predics_subdir, make_coarse,
                    use_sound_subset, remap_integers):
    """Evaluate single set of models

    Args:
        working_dir (str): path to working dir with saved data .npy files
        models_dir (str): path to models dir with saved .h5 models
        predics_subdir (str): path to directory to save model predictions
        make_coarse (bool): if True, then collapse predictions to safe/unsafe
        use_sound_subset (bool): if True, then use sound validation data subset,
            else use full validation subset
        remap_integers (bool): if True, then convert all integer tokens to the
            token for 0
    """

    (val_instances_mat, val_queries_mat, y_true
     ) = get_val_data(working_dir, get_sound=use_sound_subset)

    if remap_integers:
        # translate integers into a single value, as if they'd never been
        # seen during training
        _, _, voc, _, _ = utils.load_data(working_dir)
        remap_keys = []
        for key, val in voc.items():
            try:
                int(key)
                remap_keys.append(val)
            except ValueError:
                pass
        min_int_val = min(remap_keys)
        remap_values = {val: min_int_val for val in voc.values()
                        if val in remap_keys}

        for old, new in remap_values.items():
            val_instances_mat[val_instances_mat == old] = new
            val_queries_mat[val_queries_mat == old] = new

    if make_coarse:
        y_true = map_to_coarse(y_true)

    f1s = np.zeros(NUM_MODELS_PER_EXPERIMENT)
    recalls = np.zeros(NUM_MODELS_PER_EXPERIMENT)

    conf_num_rows = 2 if make_coarse else 4
    confusions = np.zeros(
        (NUM_MODELS_PER_EXPERIMENT, conf_num_rows, conf_num_rows))

    # get separate predics
    models = None
    separate_predics = []
    for predic_num in range(NUM_MODELS_PER_EXPERIMENT):
        if remap_integers:
            fname_fmt = 'predics_{}_remapped.npy'
        else:
            fname_fmt = 'predics_{}.npy'
        fname = fname_fmt.format(predic_num)
        path = os.path.join(predics_subdir, fname)
        if not os.path.exists(path):
            if models is None:
                models = get_models(models_dir)
            predic = models[predic_num].predict(
                [val_instances_mat, val_queries_mat])
            np.save(path, predic)
        else:
            predic = np.load(path)
        separate_predics.append(predic)

    # convert to labels for confusion
    separate_predics = [np.argmax(y_pred, axis=1) for y_pred in
                        separate_predics]
    if make_coarse:
        separate_predics = [map_to_coarse(y_pred)
                            for y_pred in separate_predics]

    # assemble metrics
    for model_num in range(NUM_MODELS_PER_EXPERIMENT):
        y_pred = separate_predics[model_num]
        if make_coarse:
            f1s[model_num] = sklearn.metrics.f1_score(y_true, y_pred)
            recalls[model_num] = sklearn.metrics.recall_score(y_true, y_pred)
        confusions[model_num] = sklearn.metrics.confusion_matrix(y_true, y_pred)

    if make_coarse:
        print("F1:")
        print(f1s)
        print(np.min(f1s), np.median(f1s), np.max(f1s))

        print("Recall:")
        print(recalls)
        print(np.min(recalls), np.median(recalls), np.max(recalls))

    print("Confusion:")
    print(confusions)
    print(np.mean(confusions, axis=0))
    print(np.median(confusions, axis=0).astype(int))


def get_memnet_predics(working_dir, models_dir, fnames=None, line_num=None):
    """Get memory network predictions

    Args:
        working_dir (str): path to working dir with data in .npy files
        models_dir (str): path to models dir with models in .h5 files
        fnames (str or list of str): filenames to get predictions from
            if None, then get them for all validation files
        line_num (int): line number to predict
            if None, then get predictions for all lines
    """
    inst, lab, _, part, paths = utils.load_data(working_dir)
    models = get_models(models_dir)

    if fnames is None:
        fnames = [paths[idx] for idx in part['validation']]
    elif isinstance(fnames, str):
        fnames = [fnames]
    elif not isinstance(fnames, list):
        raise ValueError("fnames must be str, list, or None")

    if line_num is not None:
        # -1 for line numbers starting at 1
        # -1 for excluding the #include
        line_num = line_num - 2

    val_data_generator = datagen.DataGenerator(working_dir=working_dir)

    for fname in fnames:
        print("fname: {}".format(fname))

        # get file number
        file_num = None
        for idx, path in enumerate(paths):
            if fname in path:
                file_num = idx
        if file_num is None:
            raise ValueError("Could not find file {}".format(fname))

        if line_num is not None:
            line_nums = np.array([line_num])
        else:
            line_nums = np.where(lab[file_num])[0]
        num_queries = line_nums.shape[0]
        print("Querying {} lines".format(num_queries))

        # get data matrices
        (instances_mat, queries_mat), labels_mat = (
            val_data_generator.get_samples([file_num])
        )
        y_true = np.argmax(labels_mat, axis=1)

        # get predictions
        separate_predics = []
        for predic_num in range(NUM_MODELS_PER_EXPERIMENT):
            predic = models[predic_num].predict([instances_mat, queries_mat])

            separate_predics.append(predic)

        # convert to labels
        separate_predics = [np.argmax(y_pred, axis=1) for y_pred in
                            separate_predics]

        print("labels: {}".format(y_true))
        print("predics: {}".format(separate_predics))


if __name__ == '__main__':
    working_dir = os.path.join(constants.VALIDATION_WORKING_PARENT_DIR,
                               constants.VALIDATION_WORKING_SUBDIRS[-1])
    utils.generate_sa_data(working_dir=working_dir)  # Hack to generate data

    models_dir = os.path.join(constants.VALIDATION_MODELS_PARENT_DIR,
                              constants.VALIDATION_MODELS_SUBDIRS[-1])
    predics_subdir = os.path.join(constants.VALIDATION_PREDICS_PARENT_DIR,
                                  constants.VALIDATION_PREDICS_SUBDIRS[-1])
    analyze_train_set_size( do_print_confusions=True )
    evaluate_oneoff(working_dir, models_dir, predics_subdir,
                    False, False, False)
    get_memnet_predics(working_dir, models_dir)
