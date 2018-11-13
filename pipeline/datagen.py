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
"""datagen.py: keras data generators supply training/validation examples
As in https://stanford.edu/~shervine/blog/
         keras-how-to-generate-data-on-the-fly.html
"""
import numpy as np
import keras

# if user-specific constants exist, import them and override
try:
    import user_constants as constants
except ImportError:
    import constants
import utils


class DataGenerator(object):
    """Generator to yield samples for Keras training/validation

    This DOES load the whole dataset into memory because right now it's
    small enough that it's fine. The point of this is to modularize
    yielding batches. If we get memory errors when loading, try
    reimplementing __data_generation() with np.load().
    
    Args:
        batch_size (int)
        shuffle (bool)
        working_dir (str): path to working dir where ndarrays are stored
        generate_samples_query (bool):
            if True, generate one query line and label per instance
            if False, generate all label lines per instance
        exclude_bg (bool): if True, then only give safe/unsafe lines
            (no class 0 = background from 0-padding)

    Attributes:
        batch_size (int)
        shuffle (bool)
        num_classes (int)
        generate_samples_query (bool)
        instances_mat (np.ndarray) [num_samples, max_numlines, max_linelen]
        labels_mat (np.ndarray) [num_examples, max_numlines]
        unique_labels (np.ndarray) [num_classes]
        vocab_mapping (dict)
    """
    def __init__(self, batch_size=32, shuffle=True,
                 working_dir=constants.WORKING_DIR_JULIET_DATA,
                 generate_samples_query=True, exclude_bg=True):
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.generate_samples_query = generate_samples_query

        # load data
        instances_mat, labels_mat, vocab_mapping, _, _ = utils.load_data(
                working_dir=working_dir)
        unique_labels = np.unique(labels_mat)
        self.exclude_bg = exclude_bg
        if exclude_bg:
            unique_labels = unique_labels[1:]
        self.unique_labels = unique_labels
        self.num_classes = len(self.unique_labels)
        _, self.max_numlines, self.max_linelen = instances_mat.shape
        self.instances_mat = instances_mat
        self.labels_mat = labels_mat
        self.vocab_mapping = vocab_mapping

    def generate(self, list_ids):
        """Generate batch of samples

        Args:
            list_ids (list of int): list of sample IDs

        Yields:
            for each batch, a tuple:
                if self.generate_samples_query:
                    batch_instances_mat (np.ndarray):
                        [batch_size, max_numlines, max_linelen]
                    batch_queries_mat (np.ndarray): [batch_size, 1, max_linelen]
                    batch_labels_mat (np.ndarray): [batch_size, num_classes]
                else:
                    batch_instances_mat (np.ndarray):
                        [batch_size, max_numlines, max_linelen]
                    batch_labels_mat (np.ndarray):
                        [batch_size, max_numlines, num_classes]
        """
        num_samples = len(list_ids)
        # Infinite loop
        while 1:
            # Generate order of exploration of dataset
            indexes = self.__get_exploration_order(num_samples)

            # Generate batches
            num_batches = self.get_num_batches(num_samples)
            for i in range(num_batches):
                # Find list of IDs
                batch_ids = [list_ids[k] for k in indexes[
                                    i*self.batch_size:(i+1)*self.batch_size]]

                # Generate data
                if self.generate_samples_query:
                    yield self.__gen_samples_query(batch_ids)
                else:
                    yield self.__gen_samples_full(batch_ids)

    def generate_balanced(self, list_ids):
        """Generate batch of samples s.t. batch has equal class distribution

        Args:
            list_ids (list of int): list of sample IDs

        Yields:
            for each batch, a tuple (b_i, b_q), b_l, where
                b_i = batch_instances_mat (np.ndarray)
                    [batch_size, max_numlines, max_linelen]
                b_q = batch_queries_mat (np.ndarray):
                    [batch_size, 1, max_linelen]
                b_l = batch_labels_mat (np.ndarray):
                    [batch_size, num_classes] (one-hot)
        """
        # get data subset for this partition
        part_instances_mat = self.instances_mat[list_ids]
        part_labels_mat = self.labels_mat[list_ids]

        # indexes of each class in this partition
        # key: label
        # value: array arr such that every row is (instance_idx, line_idx)
        #     s.t. labels_mat[arr[i, 0], arr[i, 1]] == label
        class_idx = dict()
        for label in self.unique_labels:
            instance_idx, line_idx = np.where(part_labels_mat == label)
            class_idx[label] = np.stack([instance_idx, line_idx], axis=1)
        
        while 1:
            for label in class_idx:
                np.random.shuffle(class_idx[label])

            batch_instances_mat = np.zeros(
                (self.batch_size, self.max_numlines, self.max_linelen))
            batch_queries_mat = np.zeros(
                (self.batch_size, 1, self.max_linelen))
            batch_labels_mat = np.zeros(
                (self.batch_size, self.num_classes))

            for batch_idx in range(self.batch_size):
                label = self.unique_labels[batch_idx % self.num_classes]
                label_examples = class_idx[label]
                # instances may repeat inside a batch,
                # if batch_size > number of class instances
                label_idx = batch_idx // self.num_classes % len(label_examples)
                label_coords = class_idx[label][label_idx]
                instance_idx, line_idx = label_coords[0], label_coords[1]
                
                batch_instances_mat[batch_idx] = (
                    part_instances_mat[instance_idx])
                batch_queries_mat[batch_idx] = (
                    part_instances_mat[instance_idx, line_idx])
                label = part_labels_mat[instance_idx, line_idx]
                if self.exclude_bg:
                    # need classes to start at 0 for to_categorical
                    label = label - 1
                batch_labels_mat[batch_idx] = keras.utils.to_categorical(
                        label,
                        num_classes=self.num_classes)

            yield([batch_instances_mat, batch_queries_mat], batch_labels_mat)

    def get_samples(self, list_ids):
        """Get all samples for these instance IDs ((instance, query), label)
        Not as a generator, just as 3 arrays

        Args:
            list_ids (list of int): list of sample IDs

        Returns: tuple
                instances_mat (np.ndarray)
                    [num_instances, max_numlines, max_linelen]
                queries_mat (np.ndarray):
                    [num_instances, 1, max_linelen]
                labels_mat (np.ndarray):
                    [num_instances, num_classes] (one-hot)
        """
        # get data subset for this partition
        part_instances_mat = self.instances_mat[list_ids]
        part_labels_mat = self.labels_mat[list_ids]

        # indexes of each class in this partition
        # key: label
        # value: array arr such that every row is (instance_idx, line_idx)
        #     s.t. labels_mat[arr[i, 0], arr[i, 1]] == label
        class_idx = dict()
        for label in self.unique_labels:
            instance_idx, line_idx = np.where(part_labels_mat == label)
            class_idx[label] = np.stack([instance_idx, line_idx], axis=1)

        num_instances = sum(arr.shape[0] for arr in class_idx.values())

        instances_mat = np.zeros(
            (num_instances, self.max_numlines, self.max_linelen))
        queries_mat = np.zeros(
            (num_instances, 1, self.max_linelen))
        labels_mat = np.zeros(
            (num_instances, self.num_classes))

        # index of each instance in result arrays
        res_idx = 0
        for label, arr in class_idx.items():
            if self.exclude_bg:
                # need classes to start at 0 for to_categorical
                label = label - 1

            for instance_idx, line_idx in arr:
                instances_mat[res_idx] = part_instances_mat[instance_idx]
                queries_mat[res_idx] = part_instances_mat[instance_idx,
                                                          line_idx]

                labels_mat[res_idx] = keras.utils.to_categorical(
                    label, num_classes=self.num_classes)

                res_idx += 1

        return [instances_mat, queries_mat], labels_mat

    def get_sound_samples(self, list_ids):
        """Get all sound samples for these instance IDs ((instance, query), label)
        Not as a generator, just as 3 arrays
        Sound samples means:
            - all the safe writes in a function before the first unsafe write
            - the first unsafe write
            - and nothing else

        Args:
            list_ids (list of int): list of sample IDs

        Returns: tuple
                instances_mat (np.ndarray)
                    [num_instances, max_numlines, max_linelen]
                queries_mat (np.ndarray):
                    [num_instances, 1, max_linelen]
                labels_mat (np.ndarray):
                    [num_instances, num_classes] (one-hot)
        """
        # get data subset for this partition
        part_instances_mat = self.instances_mat[list_ids]
        part_labels_mat = self.labels_mat[list_ids]

        safe_labels = [1, 3]
        unsafe_labels = [2, 4]

        num_files, max_numlines = part_labels_mat.shape
        print(num_files, max_numlines)

        instances = []
        queries = []
        labels = []

        for file_num in range(num_files):
            saw_unsafe = False
            for line_num in range(max_numlines):
                if saw_unsafe:
                    break

                label = part_labels_mat[file_num, line_num]
                if label in unsafe_labels:
                    saw_unsafe = True

                if label in safe_labels + unsafe_labels:
                    instances.append(part_instances_mat[file_num])
                    query = part_instances_mat[np.newaxis, file_num, line_num]
                    queries.append(query)
                    if self.exclude_bg:
                        # need classes to start at 0 for to_categorical
                        label = label - 1
                    labels.append(label)

        instances_mat = np.concatenate([inst[np.newaxis, :]
                                        for inst in instances])
        queries_mat = np.concatenate([quer[np.newaxis, :]
                                      for quer in queries])
        labels_mat = np.array(labels)
        labels_mat = keras.utils.to_categorical(
            labels_mat, num_classes=self.num_classes)

        return [instances_mat, queries_mat], labels_mat

    def get_num_batches(self, num_samples):
        """Get number of batches

        Useful for keras fit_generator(), with
        steps_per_epoch = get_num_batches(len(training_IDs))

        Args:
            num_samples (int)

        Returns:
            num_samples divided by batch size
        """
        return int(num_samples / self.batch_size)

    def __get_exploration_order(self, num_samples):
        """Generate numpy array of indexes in the order to check

        Args:
            num_samples (int)

        Returns:
            indexes (np.ndarray) [num_samples,]
        """
        # Find exploration order
        indexes = np.arange(num_samples)
        if self.shuffle:
            np.random.shuffle(indexes)

        return indexes

    def __gen_samples_query(self, batch_ids):
        """Generate each sample with a single query line

        Args:
            batch_ids (list of int): list of batch sample IDs

        Returns: tuple
            * (list of np.ndarray):
                batch_instances_mat (np.ndarray):
                    [batch_size, max_numlines, max_linelen]
                batch_queries_mat (np.ndarray): [batch_size, 1, max_linelen]
            * batch_labels_mat (np.ndarray): [batch_size, num_classes]
              one-hot array
        """
        batch_instances_mat = self.instances_mat[batch_ids]
        
        # choose a random query line from this sample
        query_idxes = np.random.randint(self.max_numlines,
                                        size=self.batch_size)
        # get the query index from each line
        batch_queries_mat = batch_instances_mat[np.arange(self.batch_size),
                                                query_idxes]
        # reshape
        batch_queries_mat = batch_queries_mat[:, np.newaxis, :]

        batch_labels_mat = self.labels_mat[batch_ids]
        batch_labels_mat = batch_labels_mat[np.arange(self.batch_size),
                                            query_idxes]
        batch_labels_mat = keras.utils.to_categorical(
            batch_labels_mat, num_classes=self.num_classes)

        return [batch_instances_mat, batch_queries_mat], batch_labels_mat

    def __gen_samples_full(self, batch_ids):
        """Generate each sample with all lines

        Label for each instance is a vector of labels for all lines.
        Note that this does NOT account for class imbalance.

        Args:
            batch_ids (list of int): list of batch sample IDs

        Returns: tuple
            * batch_instances_mat (np.ndarray):
                  [batch_size, max_numlines, max_linelen]
            * batch_labels_mat (np.ndarray):
                  [batch_size, max_numlines, num_classes]
                  one-hot array
        """
        batch_instances_mat = self.instances_mat[batch_ids]
        batch_labels_mat = self.labels_mat[batch_ids]
        batch_labels_mat = keras.utils.to_categorical(
                batch_labels_mat, num_classes=self.num_classes)
        return batch_instances_mat, batch_labels_mat


def _test_gen_samples_full(batch_size, list_ids, instances_shape,
                           working_dir):
    gen = DataGenerator(batch_size=batch_size, generate_samples_query=False,
                        exclude_bg=False, working_dir=working_dir)
    num_classes = gen.num_classes
    gen = gen.generate(list_ids)

    for _ in range(5):
        batch_instances_mat, batch_labels_mat = next(gen)
        assert(batch_instances_mat.shape ==
               (batch_size, instances_shape[1], instances_shape[2]))
        assert(batch_labels_mat.shape ==
               (batch_size, instances_shape[1], num_classes))
        # NOTE also checked that the batches are correctly sliced out
        # of the data, but had to remove this test since keras datagens
        # only allow returning input/output data


def _test_gen_samples_query(batch_size, list_ids, instances_shape,
                            working_dir):
    gen = DataGenerator(batch_size=batch_size, generate_samples_query=True,
                        exclude_bg=False, working_dir=working_dir)
    num_classes = gen.num_classes
    gen = gen.generate(list_ids)

    for _ in range(5):
        inputs, batch_labels_mat = next(gen)
        batch_instances_mat = inputs[0]
        batch_queries_mat = inputs[1]
        assert(batch_instances_mat.shape ==
               (batch_size, instances_shape[1], instances_shape[2]))
        assert(batch_queries_mat.shape ==
               (batch_size, 1, instances_shape[2]))
        assert(batch_labels_mat.shape ==
               (batch_size, num_classes))
        # NOTE also checked that the batches are correctly sliced out
        # of the data, but had to remove this test since keras datagens
        # only allow returning input/output data


def _test_gen_balanced(batch_size, list_ids, instances_shape,
                       working_dir):
    gen = DataGenerator(batch_size=batch_size, working_dir=working_dir)
    num_classes = gen.num_classes
    gen = gen.generate_balanced(list_ids)

    for _ in range(5):
        inputs, batch_labels_mat = next(gen)
        batch_instances_mat = inputs[0]
        batch_queries_mat = inputs[1]
        assert(batch_instances_mat.shape ==
               (batch_size, instances_shape[1], instances_shape[2]))
        assert(batch_queries_mat.shape ==
               (batch_size, 1, instances_shape[2]))
        assert(batch_labels_mat.shape ==
               (batch_size, num_classes))
        labels_flat = np.argmax(batch_labels_mat, axis=1)

        # check that the sampling is balanced
        idx = 2 * num_classes
        # e.g. [0, 1, 2, 0, 1, 2] for 3 classes
        expected = list(range(num_classes)) * 2
        assert(np.array_equal(labels_flat[:idx], np.array(expected)))


def _test():
    batch_size = 32
    working_dir = constants.TEST_WORKING_DIR
    instances_mat, labels_mat, _, partition, _ = utils.load_data(
        working_dir=working_dir)
    list_ids = partition['validation']
    instances_shape = instances_mat.shape
    _test_gen_samples_full(batch_size, list_ids, instances_shape, working_dir)
    _test_gen_samples_query(batch_size, list_ids, instances_shape, working_dir)
    _test_gen_balanced(batch_size, list_ids, instances_shape, working_dir)


# _test() # This relies on npy stuff not yet created. 
