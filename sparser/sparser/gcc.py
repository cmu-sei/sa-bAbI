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
import re
import codecs

from .model import Diagnostic, Message, Location, ToolInfo
from .parser import Parser, register_parser


class GccWarningParser(Parser):
    """A parser for warnings from the gcc/g++ compiler
    
    This class parses warnings produced by the gcc or g++ compiler.
    A regular expression is used to recognize warning messages in
    the input file. The recommended gcc invocation is::

        gcc -O2 -fmessage-lengh=0 -Wall -Wextra -Wpendantic <srcfile> 2> output.txt
    
    The resulting "output.txt" can then be consumed by this parser.
    """

    # NOTE:
    # Column numbers and switches (e.g. -Wnull-dereference) are technically
    # optional in the GCC warning output, though we very much would prefer
    # if the users of this didn't omit them in their gcc output (e.g. by
    # setting compiler flags like -fno-show-column). In fact, this regex
    # current _requires_ both column and switch to be present.
    message_regex = re.compile(("^"
                                "(?P<path>\S.*?):"
                                "(?P<line>\d+):"
                                "(?P<column>\d*):\s*"
                                "(?P<type>warning|note):\s*"
                                "(?P<message>.*?)\s*"
                                "\[(?P<switch>\-W.+)\]\s*$"))
    """str: regex for matching gcc warnings"""

    def load_iter(self, input_file):
        """Generate diagnostics from gcc/g++ warning output

        Args:
            input_file (binary file-like object): A binary file-like object 
            containing gcc/g++ compiler warnings.

        Returns:
            An iterator of Diagnostic objects
        
        TODO: There is a little bit more nuance to gcc warnings than is
        fully captured here. (Nuance may be a euphemism for irritating
        gaps in consistency.) A fully-featured parser would likely handle
        edge cases such as warnings that span multiple messages.
        """
        reader = codecs.getreader("utf-8")
        for line in reader(input_file):
            m = self.message_regex.match(line.strip())
            if m is not None:
                yield Diagnostic(
                    tool_info=ToolInfo(name="gcc"),
                    kind=m.group("switch"),
                    message=Message(
                        text=m.group("message"),
                        location=Location(
                            path=m.group("path"),
                            line_start=int(m.group("line")))))


register_parser(
    name="gcc_warnings",
    tool_name="gcc",
    input_type="text/plain",
    description="Parses textual warning output from gcc/g++.",
    cls=GccWarningParser)
