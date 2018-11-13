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
import os
import json
import subprocess
import re
import collections
import random

def process_directory(
        rootdir,
        find_symbols_exe,
        cargs):
    testcase_info = collections.defaultdict(list)
    for root, dirs, files in os.walk(rootdir):
        for f in files:
            match = re.match("^(?P<id>CWE(?P<cwe>[0-9]*)_.*[0-9]+)[a-z]?\.c$", f)
            if match:
                source_file = {}
                cwe = match.group('cwe')
                testid = match.group('id')
                abspath = os.path.join(root, f)
                source_file["path"] = abspath

                cmd = [find_symbols_exe, abspath] + cargs
                find_symbols = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE)

                out, err = find_symbols.communicate()
                if err.strip() != "":
                    print err
                source_file["symbols"] = json.loads(out)["symbols"]        
                testcase_info[testid].append(source_file)
    return testcase_info

def to_json(testcase_info):
    json_data= []
    for id in testcase_info:
        testcase_data = {}
        testcase_data["id"] = id
        testcase_data["sources"] = testcase_info[id]
        json_data.append(testcase_data)
    return json.dumps(json_data, indent=4, sort_keys=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("rootdir")
    parser.add_argument("outfile")
    parser.add_argument("--includes", nargs="+", default=[])
    parser.add_argument("--defines", nargs="+", default=[])
    parser.add_argument("--find_symbols_exe", default = "find_symbols")
    args = parser.parse_args()

    include_args = ["-I" + inc for inc in args.includes]
    define_args = ["-D" + dfn for dfn in args.defines]
    cargs = include_args + define_args

    database = process_directory(args.rootdir, args.find_symbols_exe, cargs)
    with open(args.outfile, 'wb') as f:
        f.write(to_json(database))
