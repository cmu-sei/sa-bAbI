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
"""sa_tag.py: defines the Tag class for SA-bAbI"""
import enum

class Tag(enum.Enum):
    """Tags for each line of each instance representing buffer write safety

    e.g.
    void fun()                                               | OTHER
    {                                                        | OTHER
        char entity_3[30];                                   | BODY
        char entity_2[40];                                   | BODY
        int entity_1;                                        | BODY
        int entity_8;                                        | BODY
        int entity_7;                                        | BODY
        entity_1 = 45;                                       | BODY
        entity_7 = 34;                                       | BODY
        for(entity_8 = 46; entity_8 < entity_1; entity_8++){ | BODY
        }                                                    | BODY
        entity_2[entity_7] = 'N';                            | BUFWRITE_TAUT_SAFE
        entity_3[entity_8] = 'e';                            | BUFWRITE_COND_UNSAFE
    }                                                        | OTHER

    """
    # Function wrapping lines
    OTHER = 0
    # Lines inside body that aren't buffer writes
    BODY = 1
    # Buffer write that requires control flow analysis to prove safe
    BUFWRITE_COND_SAFE = 2
    # Buffer write that requires control flow analysis to prove unsafe
    BUFWRITE_COND_UNSAFE = 3
    # Buffer write that is provably safe even without control flow
    BUFWRITE_TAUT_SAFE = 4
    # Buffer write that is provably unsafe even without control flow
    BUFWRITE_TAUT_UNSAFE = 5
