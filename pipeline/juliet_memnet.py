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
"""juliet_memnet.py: minimal working example memory network on Juliet"""
from keras.engine.topology import Layer
from keras.models import Model, Sequential
from keras.layers import Input, Embedding, Activation
from keras.layers import BatchNormalization
from keras.layers import Lambda, Dropout
from keras.layers import add, dot, Permute, Dense, Reshape
from keras import backend as K

import numpy as np

# if user-specific constants exist, import them and override
try:
    import user_constants as constants
except ImportError:
    import constants
import utils
import datagen


# other options: constants.WORKING_DIR_CHOI_DATA
#                constants.WORKING_DIR_JULIET_DATA
working_dir = constants.WORKING_DIR_SA_DATA

utils.generate_sa_data() # Hack to generate data
instances_mat, labels_mat, vocab_mapping, partition, _ = utils.load_data(
        working_dir=working_dir)

_, max_numlines, max_linelen = instances_mat.shape
vocab_size = len(vocab_mapping) + 1

data_generator = datagen.DataGenerator(batch_size=36, working_dir=working_dir)
# 0 background
# 1 safe
# 2 unsafe
num_classes = data_generator.num_classes

# embedding dimension for memnet
# ideally this would be in the scope of get_model(), but
# keras.models.load_model() only works with the custom layers if they
# don't have any arguments
embed_dim = 32


def get_pos_enc_mat(max_linelen, embed_dim):
    """Get Sukhbaatar2015 position encoding matrix "l"

    Args:
        max_linelen (int)
        embed_dim (int)

    Returns:
        position_encoding_mat (np.ndarray) [max_linelen, embed_dim]
    """
    position_encoding_mat = np.outer(
        1 - 2 * (np.arange(max_linelen) + 1) / max_linelen,
        -(np.arange(embed_dim) + 1) / embed_dim
        ) + (1 - (np.arange(max_linelen) + 1) / max_linelen)[:, np.newaxis]

    return position_encoding_mat


def position_encode(embedded_instances, pos_enc_mat):
    """Sukhbaatar2015 position encoding

    Inputs:
        embedded_instances (tensor)
            [None, max_numlines, max_linelen, embed_dim]
        pos_enc_mat (np.ndarray) from get_pos_enc_mat
            [max_linelen, embed_dim]

    Outputs:
        pos_enc_instances (tensor)
            [None, max_numlines, embed_dim]
    """
    pos_enc_instances = (embedded_instances *
                         pos_enc_mat[np.newaxis, np.newaxis, :, :])
    pos_enc_instances = K.sum(pos_enc_instances, axis=2)
    return pos_enc_instances


def bow_encode(embedded_instances):
    """bag-of-words encoding (just a sum)

    Inputs:
        embedded_instances (tensor)
            [None, max_numlines, max_linelen, embed_dim]

    Outputs:
        bow_instances (tensor)
            [None, max_numlines, embed_dim]
    """
    bow_instances = K.sum(embedded_instances, axis=2)
    return bow_instances


class BowEncode(Layer):
    """Bag-of-words encode by summing across dimension 2"""

    def __init__(self, **kwargs):
        self.axis = 2
        super(BowEncode, self).__init__(**kwargs)

    def build(self, input_shape):
        super(BowEncode, self).build(input_shape)

    def call(self, x):
        return K.sum(x, axis=self.axis)

    def compute_output_shape(self, input_shape):
        return input_shape[:self.axis] + input_shape[self.axis + 1:]


class PositionEncode(Layer):
    """Position encoding (Sukhbaatar2015)"""

    def __init__(self, **kwargs):
        self.pos_enc_mat = get_pos_enc_mat(max_linelen, embed_dim)
        super(PositionEncode, self).__init__(**kwargs)

    def build(self, input_shape):
        super(PositionEncode, self).build(input_shape)

    def call(self, x):
        pos_enc_instances = x * self.pos_enc_mat[np.newaxis, np.newaxis, :, :]
        pos_enc_instances = K.sum(pos_enc_instances, axis=2)
        return pos_enc_instances

    def compute_output_shape(self, input_shape):
        # removes the 2-axis
        return input_shape[:2] + input_shape[2 + 1:]


def get_model():
    num_hops = 3
    num_final_dense_layers = 0
    use_position_encoding = True
    use_internal_layer = True
    use_batch_normalization = True

    # placeholders
    # (None, story_maxlen, story_maxlinelen)
    input_lines = Input((max_numlines, max_linelen))
    # (None, query_maxlen, query_maxlinelen)
    query_line = Input((1, max_linelen))

    # encoders
    def get_encoder(embed_dim):
        """Returns a layer that embeds each story line into an embed_dim vector.

        Input to this layer is shape (None, num_lines, line_maxlen)
        Output of this layer is shape (None, num_lines, embed_dimension)
        """
        encoder = Sequential()
        # (None, story_maxlen, story_maxlinelen, embed_dim)
        encoder.add(Embedding(vocab_size, embed_dim))
        if use_position_encoding:
            encoder.add(PositionEncode())
        else:
            encoder.add(BowEncode())
        encoder.add(Dropout(0.3))
        return encoder

    input_encoder_val = get_encoder(embed_dim)
    input_encoder_addr = get_encoder(embed_dim)

    # encoding
    # (None, story_maxlen, embed_dim)
    input_encoded_val = input_encoder_val(input_lines)
    # (None, story_maxlen, embed_dim)
    input_encoded_addr = input_encoder_addr(input_lines)
    # (None, 1, embed_dim)
    query_encoded = input_encoder_addr(query_line)

    query = query_encoded

    for _ in range(num_hops):
        # (None, story_maxlen, 1)
        match = dot([input_encoded_addr, query], axes=(2, 2))

        # permute/softmax/permute is really just softmax
        match = Permute((2, 1))(match)
        atten = Activation('softmax')(match)
        # (None, story_maxlen, 1)
        atten = Permute((2, 1))(atten)

        # (None, embed_dim, 1)
        response = dot([atten, input_encoded_val], 0)
        # (None, embed_dim)
        response = Reshape((embed_dim,))(response)

        if use_internal_layer:
            # internal learnable layer
            response = Dense(embed_dim)(response)

        if use_batch_normalization:
            response = BatchNormalization()(response)

        query = add([query, response])

    for _ in range(num_final_dense_layers):
        response = Dense(embed_dim)(response)
        response = Dropout(0.5)(response)

    # classification layer
    answer = Dense(num_classes)(response)
    answer = Activation('softmax')(answer)

    model = Model([input_lines, query_line], answer)
    return model
