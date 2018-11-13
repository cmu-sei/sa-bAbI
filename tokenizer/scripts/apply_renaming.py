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
import sys
import random

def apply_renamings(symbol_database, outdir, clang_rename_exe, cargs):
    for tc in symbol_database:
        for src_file in tc["sources"]:
            renamings = []
            for symbol in src_file["symbols"]:
                if symbol["kind"] in "TypedefDecl":
                    continue
                if "rename" in symbol:
                    renamings.append((symbol["offset"], symbol["rename"]))

            src_path = src_file["path"]
            command = [clang_rename_exe]
            for renaming in renamings:
                offset, new_name = renaming    
                command.append("-offset=" + str(offset))
                command.append("-new-name=" + new_name)
            command.append(src_path)
            command.append("--")
            command = command + cargs
            
            root, base = os.path.split(src_path)
            outfile = os.path.join(outdir, base)
            with open(outfile, 'wb') as f:
                p = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if err.strip() != "":
                    sys.stderr.write(err + "\n") 
                    sys.stderr.write(" ".join(command))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("symbol_database")
    parser.add_argument("outdir")
    parser.add_argument("--includes", nargs="+", default=[])
    parser.add_argument("--defines", nargs="+", default=[])
    parser.add_argument("--clang_rename_exe", default="clang-rename")
    args = parser.parse_args()

    include_args = ["-I" + inc for inc in args.includes]
    define_args = ["-D" + dfn for dfn in args.defines]
    cargs = include_args + define_args

    with open(args.symbol_database, 'rb') as f:
        data = json.load(f)

    apply_renamings(data, args.outdir, args.clang_rename_exe, cargs)
