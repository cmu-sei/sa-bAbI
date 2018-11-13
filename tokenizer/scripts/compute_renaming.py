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

def get_new_name(kind, counter):
    return "{0}{1}".format(kind.replace("Decl", ""), counter) 

def compute_renamings_flat(symbol_database, preserve_main=True):
    for testcase in symbol_database:
        # A dictionary that remembers the names externally linked
        # symbols have taken on
        global_renamings = {}

        # This set is meant to be equivalent in content to 
        # global_renamings.values(). At times we will need 
        # to determine if a given name has been claimed 
        # by a symbol with external linkage. This requires
        # a reverse lookup in the global_renamings dict,
        # which we could do directly by interrogating its
        # values, however maintaining a separate set might
        # be slightly faster.
        used_global_names = set()
        
        for src_file in testcase["sources"]:
            symbols = list(src_file["symbols"])
            random.shuffle(symbols)
            counter = 0

            for symbol in symbols:
                name = symbol["text"]
                offset = symbol["offset"]
                kind = symbol["kind"]
                linkage = symbol["linkage"]
                text = symbol["text"]
               
                if preserve_main:
                    if kind == "FunctionDecl" and name == "main":
                        continue
                    if kind == "ParmDecl" and (name == "argc" or name == "argv"):
                        continue

                if text.strip() == "":
                    continue

                if linkage == 4 and name in global_renamings:
                    symbol["rename"] = global_renamings[name]
                else:
                    # Increment our counter until we find a name 
                    # that isn't in use. A given name might already
                    # be claimed by a symbol with external linkage
                    found_name = False
                    while not found_name:
                        new_name = get_new_name(kind, counter)
                        counter += 1
                        if new_name not in used_global_names:
                            found_name = True
                    symbol["rename"] = new_name
                    
                    if linkage == 4:
                        global_renamings[name] = new_name
                        used_global_names.add(new_name)

                        
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("symbol_database")
    parser.add_argument("--strategy", choices=["flat"], default="flat")
    parser.add_argument("--out")
    args = parser.parse_args()

    with open(args.symbol_database, 'rb') as f:
        data = json.load(f)

    if args.strategy == "flat":
        compute_renamings_flat(data)

    outfile = args.symbol_database
    if args.out is not None:
        outfile = args.out

    with open(outfile, 'wb') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
