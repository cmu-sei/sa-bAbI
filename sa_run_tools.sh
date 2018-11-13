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

runnable_tools="clang_sa frama-c cppcheck"

if [ "$#" -lt 1 ]; then
    echo "Usage: sa_run_tools.sh <working_dir> <tool1> <tool2> ..."
    echo "e.g.: sa_run_tools.sh ./data cppcheck"
    for tool in $runnable_tools; do
	echo $tool
    done
    exit
fi

working_dir=$(realpath $1)
export DATA_DIR=$working_dir

script="cd /mnt/data/src && ls | parallel --will-cite --ungroup analyze_file.sh {}"
for service_name in "${@:2}"; do
    echo ++++Running tool: $service_name.
    start_time=$(date +%s)

    mkdir -p $working_dir/$service_name
    DATA_DIR=$working_dir docker-compose run \
        --rm $service_name \
        bash -c "$script /mnt/data/$service_name"

    end_time=$(date +%s)
    echo Done running $service_name, took: $(expr $end_time - $start_time) seconds
    echo Output is in: $working_dir/$service_name
done
