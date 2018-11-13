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

"""train.py: train memory network on juliet"""
import os

import keras.optimizers
import numpy as np
import sklearn.metrics

# if user-specific constants exist, import them and override
try:
    import user_constants as constants
except ImportError:
    import constants
import datagen
import utils

import juliet_memnet

# other options: constants.WORKING_DIR_CHOI_DATA
#                constants.WORKING_DIR_JULIET_DATA
working_dir = constants.WORKING_DIR_SA_DATA

instances_mat, labels_mat, _, partition, _ = utils.load_data(
    working_dir=working_dir)

_, max_numlines, _ = instances_mat.shape

data_generator = datagen.DataGenerator(batch_size=36, working_dir=working_dir)
num_classes = data_generator.num_classes


def run_experiments(num_experiments=10, models_dir=None):
    """
    Args:
        num_experiments (int): how many separate models to train
        models_dir (str): if a path to a directory is given, save each
            model there

            To load:
            custom_objects = {'PositionEncode': juliet_memnet.PositionEncode}
            mod = keras.models.load_model(path, custom_objects=custom_objects)
    """

    # get train params
    steps_per_epoch = data_generator.get_num_batches(len(partition['train']))
    validation_steps = data_generator.get_num_batches(
        len(partition['validation']))

    # get validation data
    val_data_generator = datagen.DataGenerator(
        batch_size=1000, working_dir=working_dir)
    (val_instances_mat, val_queries_mat), val_labels_mat = next(
        val_data_generator.generate_balanced(partition['validation']))
    y_true = np.argmax(val_labels_mat, axis=1)

    cnf_matrices = np.zeros((num_experiments, num_classes, num_classes))

    for experiment_num in range(num_experiments):
        print("=====Beginning experiment %s of %s=====" %
              (experiment_num + 1, num_experiments))

        # get untrained model
        model = juliet_memnet.get_model()
        model.compile(loss='categorical_crossentropy',
                      optimizer=keras.optimizers.Adam(lr=0.001))

        # train
        model.fit_generator(
            data_generator.generate_balanced(partition['train']),
            steps_per_epoch=steps_per_epoch,
            validation_data=data_generator.generate_balanced(
                partition['validation']),
            validation_steps=validation_steps,
            epochs=30)

        # predict
        predics = model.predict([val_instances_mat, val_queries_mat])
        predics = np.argmax(predics, axis=1)

        # metrics
        cnf_matrix = sklearn.metrics.confusion_matrix(y_true, predics)
        print(cnf_matrix)
        cnf_matrices[experiment_num] = cnf_matrix

        # save model
        if models_dir:
            if not os.path.isdir(models_dir):
                print("Invalid models directory '{}', could not save "
                      "model".format(models_dir))
            else:
                fname = "model_{}.h5".format(experiment_num)
                path = os.path.join(models_dir, fname)
                print(path)
                model.save(path)

    print("Confusion matrix mean:")
    print(np.mean(cnf_matrices, axis=0))
    print("Confusion matrix standard deviation:")
    print(np.std(cnf_matrices, axis=0))


run_experiments(num_experiments=10, models_dir=constants.MODELS_DIR)
