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
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import codecs

from .model import Diagnostic, Message, Location, ToolInfo
from .parser import Parser, register_parser


class FramacWarningParser(Parser):
    """A parser for warnings from the Frama-c tool
    
    This class parses warnings produced by the Frama-c abstract
    interpretation toolkit. A regular expression is used to recognize 
    warning messages 

    TODO: Add recommended invocations
    """

    message_regex = re.compile(("^"
                                "(?P<path>\S.*?):"
                                "(?P<line>\d+):\s*"
                                "\[(?P<module>\S.*?)\]\s*"
                                "(?P<kind>warning|note):\s*"
                                "(?P<message>.*?)\s*$"))
    """str: regex for matching frama-c warnings"""

    def load_iter(self, input_file):
        """Generates diagnostics from frama-c warning output

        Args:
            input_file (binary file-like object): A binary file-like object 
            containing frama-c output.

        Returns:
            An iterator of Diagnostic objects
        """
        tool_info = ToolInfo(name="frama-c")

        reader = codecs.getreader("utf-8")
        for line in reader(input_file):
            match = self.message_regex.match(line.strip())
            if match:
                yield Diagnostic(
                    tool_info=tool_info,
                    kind=match.group("module"),
                    message=Message(
                        text=match.group("message"),
                        location=Location(
                            path=match.group("path"),
                            line_start=match.group("line"))))


register_parser(
    name="framac_warnings",
    tool_name="frama-c",
    input_type="text/plain",
    description="Parses textual warning output from frama-c modules.",
    cls=FramacWarningParser)
