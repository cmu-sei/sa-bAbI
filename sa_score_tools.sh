if [ "$#" -ne 1 ]; then
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
    echo "Usage: sa_score_tools.sh <working_dir>"
    echo "e.g.: sa_score_tools.sh ./data"
    exit
fi

working_dir=$(realpath $1)

validation_arg=""
if [ -f "$working_dir/validation_set" ]; then
    validation_arg="--validation_set /mnt/data/validation_set"
fi

DATA_DIR=$working_dir docker-compose run --rm sababi bash -c "\
    python /sa_babi/score_tool_outputs.py $validation_arg \
    -v \
    /mnt/data/manifest.json \
    /sa_babi/checkers.yaml \
    /mnt/data/alerts/*.csv \
    > /mnt/data/tool_confusion_matrix.csv \
    2> /mnt/data/score_all.log"


DATA_DIR=$working_dir docker-compose run --rm sababi bash -c "\
    python /sa_babi/score_tool_outputs.py $validation_arg \
    --sound_only\
    -v \
    /mnt/data/manifest.json \
    /sa_babi/checkers.yaml \
    /mnt/data/alerts/*.csv \
    > /mnt/data/tool_confusion_matrix_sound.csv \
    2> /mnt/data/score_sound.log"
