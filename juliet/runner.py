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
import xml.etree.ElementTree as ET
import os


def build_file_index(start):
    file_index = dict()
    for root, dirs, files in os.walk(start):
        for name in files:
            path = os.path.join(root, name)
            file_index[name] = path
    return file_index


def iter_test_cases(manifest_file, cwes, file_index):
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    for testcase in root.iter("testcase"):
        src_files = []
        headers = []
        match = False

        for testfile in testcase.iter("file"):
            name = testfile.get("path").strip()
            if name not in file_index:
                continue
            path = file_index[name]
            if path.endswith(".h"):
                headers.append(path)
            else:
                if path.endswith(".cpp"):
                    match = False
                    break
                src_files.append(path)

            for flaw in testfile.iter("flaw"):
                cwe_str = flaw.get("name").split(":")[0]
                cwe = int(cwe_str.replace("CWE-", "").lstrip("0"))
                if cwe in cwes:
                    match = True

        if match:
            yield (src_files, headers)


def main(handler):
    import sys
    juliet_c_dir = sys.argv[1]
    outdir = sys.argv[2]
    cwes = set([int(x) for x in sys.argv[3:]])
    manifest_file = os.path.join(juliet_c_dir, "manifest.xml")
    tc_support = os.path.join(juliet_c_dir, "testcasesupport")
    src_dir = os.path.join(juliet_c_dir, "testcases")
    file_index = build_file_index(juliet_c_dir)

    for tc in iter_test_cases(manifest_file, cwes, file_index):
        handler(tc, tc_support, outdir)
