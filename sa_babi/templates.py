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
"""templates.py: Templates for SA-bAbI code generation"""

BUFWRITE_LINES = ["$buf_var[$idx_var] = '$char';"]

# templates for functions without free variables

COND_DEC_INIT_PAIRS = [
    ("char $buf_var[$buf_len];", None),
    ("int $idx_var;", "$idx_var = $idx_init;"),
    ("int $thresh_var;", "$thresh_var = $thresh;")
]
COND_MAIN_LINES = [
    "if($idx_var < $thresh_var){",
    "$idx_var = $true_idx;",
    "} else {",
    "$idx_var = $false_idx;",
    "}"
]

WHILE_DEC_INIT_PAIRS = [
    ("char $buf_var[$buf_len];", None),
    ("int $idx_var;", "$idx_var = $idx_init;"),
    ("int $max_var;", "$max_var = $max_idx;")
]
WHILE_MAIN_LINES = [
    "while($idx_var < $max_var){",
    "$idx_var++;",
    "}"
]

FOR_DEC_INIT_PAIRS = [
    ("char $buf_var[$buf_len];", None),
    ("int $idx_var;", None),
    ("int $max_var;", "$max_var = $max_idx;")
]
FOR_MAIN_LINES = [
    "for($idx_var = $idx_init; $idx_var < $max_var; $idx_var++){",
    "}"
]

# templates for functions with one free variable

COND_FV_DEC_INIT_PAIRS = [
    ("int $idx_var;", "$idx_var = rand();"),
    ("char $buf_var[$buf_len];", None),
    ("int $chk_var;", "$chk_var = $chk;")
]
COND_FV_MAIN_LINES = [
    "if($idx_var < $chk_var){",
    "} else {",
    "$idx_var = $false_idx;",
    "}"
]

WHILE_FV_DEC_INIT_PAIRS = [
    ("char $buf_var[$buf_len];", None),
    ("int $idx_var;", "$idx_var = $idx_init;"),
    ("int $chk_var;", "$chk_var = $chk;"),
    ("int $max_var;", "$max_var = rand();")
]
WHILE_FV_MAIN_LINES = [
    "if ($max_var < $chk_var){",
    "} else {",
    "$max_var = $false_idx;",
    "}",
    "while($idx_var < $max_var){",
    "$idx_var++;",
    "}"
]

FOR_FV_DEC_INIT_PAIRS = [
    ("char $buf_var[$buf_len];", None),
    ("int $idx_var;", None),
    ("int $chk_var;", "$chk_var = $chk;"),
    ("int $max_var;", "$max_var = rand();")
]
FOR_FV_MAIN_LINES = [
    "if ($max_var < $chk_var){",
    "} else {",
    "$max_var = $false_idx;",
    "}",
    "for($idx_var = $idx_init; $idx_var < $max_var; $idx_var++){",
    "}"
]

# main function body wrapper

FUNC_TMPL_STR = """#include <stdlib.h>
int main()
{
$body
    return 0;
}"""
