# SA-bAbI dataset documentation
Carson Sestili, William Snavely, Nathan VanHoudnos

# Instance Types
## Conditional
## While Loop
## For Loop
## Conditional with Indeterminate Variable
## While Loop with Indeterminate Variable
## For Loop with Indeterminate Variable

# Vulnerability Types
## Flow-Sensitive
## Flow-Insensitive

# Design Choices
## A small subset of C

# How Each Instance is Generated

# Instance metadata
The `generate.py` script can produce simple, json metadata for the instances
it generates. This is done by specifying the `-manifest_file` option, along
with the path to a file while shall store the metadata. The format of
this metadata is:

```
{
    "working_dir": (string) The directory where the files were generated
    "num_instances" : (int) the number of instances generated
    "tags": {
        "<instance_id>": [ (int)line 1 tag, (int)line 2 tag, ... ]
    }
}
```

Above, `<instance_id>` refers to the unique hash identifier for a generated
instance. Each instance has a list of integer tags associated with it.
Index I of this tag list represents the tag for line I of the instance.
These integers correspond to the Tag enum defined in generate.py.

# Document markings
```
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
```
