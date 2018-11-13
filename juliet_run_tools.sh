#!/usr/bin/env bash
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
if [ "$#" -ne 1 ]; then
    echo "Usage: juliet_run_tools.sh <working_dir>"
    exit
fi

working_dir=$(realpath $1)
mkdir -p $working_dir

juliet_url=https://samate.nist.gov/SRD/testsuites/juliet/Juliet_Test_Suite_v1.3_for_C_Cpp.zip
if [ ! -d "$working_dir/src" ]; then
    mkdir $working_dir/src
    pushd $working_dir/src
    wget $juliet_url
    unzip Juliet_Test_Suite_v1.3_for_C_Cpp.zip
    popd
fi

mkdir -p $working_dir/alerts

echo "Running cppcheck"
mkdir -p $working_dir/cppcheck
begin=$(date +%s)
DATA_DIR=$working_dir docker-compose run --rm \
    -v $(pwd)/juliet:/juliet cppcheck \
    bash -c "python /juliet/cppcheck.py /mnt/data/src/C /mnt/data/cppcheck 121"
DATA_DIR=$working_dir docker-compose run --rm tool_parser \
    bash -c "find /mnt/data/cppcheck -type f | xargs sparser cppcheck_xml" \
    > $working_dir/alerts/cppcheck.csv
end=$(date +%s)
echo Done, took: $(expr $end - $begin) seconds     

echo "Running clang_sa"
mkdir -p $working_dir/clang_sa
begin=$(date +%s)
DATA_DIR=$working_dir docker-compose run --rm \
    -v $(pwd)/juliet:/juliet clang_sa \
    bash -c "python /juliet/clang_sa.py /mnt/data/src/C /mnt/data/clang_sa 121"
DATA_DIR=$working_dir docker-compose run --rm tool_parser \
    bash -c "find /mnt/data/clang_sa -type f | xargs sparser clang_sa_plist" \
    > $working_dir/alerts/clang_sa.csv
end=$(date +%s)
echo Done, took: $(expr $end - $begin) seconds     

echo "Running frama-c"
mkdir -p $working_dir/frama-c
begin=$(date +%s)
DATA_DIR=$working_dir docker-compose run --rm \
    -v $(pwd)/juliet:/juliet frama-c \
    bash -c "python /juliet/frama-c.py /mnt/data/src/C /mnt/data/frama-c 121"
DATA_DIR=$working_dir docker-compose run --rm tool_parser \
    bash -c "find /mnt/data/frama-c -type f | xargs sparser framac_warnings" \
    > $working_dir/alerts/frama-c.csv
end=$(date +%s)
echo Done, took: $(expr $end - $begin) seconds

DATA_DIR=$working_dir docker-compose run --rm juliet \
    bash -c "python /juliet/score_tool_outputs.py \
        /mnt/data/src/C/manifest.xml \
        /juliet/checkers.yaml \
        /mnt/data/alerts/*.csv > /mnt/data/tool_confusion_matrix.csv"  
