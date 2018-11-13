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
import plistlib
import codecs

from .parser import Parser, register_parser
from .model import Diagnostic, Message, Location, ToolInfo


class ClangWarningParser(Parser):
    """A parser for warnings from the clang compiler
    
    This class parses warnings produced by the clang c/c++ compiler.
    A regular expression is used to recognize warning messages in
    the input file. The recommended clang invocation is::

        clang -fmessage-lengh=0 -Weverything <srcfile> 2> output.txt
    
    The resulting "output.txt" can then be consumed by this parser.
    """

    message_regex = re.compile(("^"
                                "(?P<path>\S.*?):"
                                "(?P<line>\d+):"
                                "(?P<column>\d*):\s*"
                                "(?P<type>warning|note):\s*"
                                "(?P<message>.*?)\s*"
                                "\[(?P<switch>\-W.+)\]\s*$"))
    """str: regex for matching clang warnings"""

    def load_iter(self, input_file):
        """Generates diagnostics from clang warning output

        Args:
            input_file (binary file-like object): A binary file-like object 
            containing clang compiler warnings.

        Returns:
            An iterator of Diagnostic objects
        """
        tool_info = ToolInfo(name="clang")

        reader = codecs.getreader("utf-8")
        for line in reader(input_file):
            m = self.message_regex.match(line.strip())
            if m is not None:
                yield Diagnostic(
                    tool_info=tool_info,
                    kind=m.group("switch"),
                    message=Message(
                        text=m.group("message"),
                        location=Location(
                            path=m.group("path"),
                            line_start=int(m.group("line")))))


register_parser(
    name="clang_warnings",
    tool_name="clang",
    input_type="text/plain",
    description="Parses textual warning output from the clang compiler.",
    cls=ClangWarningParser)


class ClangAnalyzerPlistParser(Parser):
    def load_iter(self, input_file):
        plist_data = plistlib.readPlist(input_file)

        # File names are stored in the following dictionary
        file_dict = plist_data['files']

        clang_version = plist_data.get('clang_version')
        tool_info = ToolInfo(name="clang_sa", version=clang_version)
        for entry in plist_data['diagnostics']:
            diag = Diagnostic(tool_info=tool_info, kind=entry["category"])

            # We need to look up the file name aforementioned dictionary
            location = entry["location"]
            file_key = entry["location"]["file"]
            file_name = file_dict[file_key]

            diag.message = Message(
                text=entry["description"],
                location=Location(path=file_name, line_start=location["line"]))

            yield diag


register_parser(
    name="clang_sa_plist",
    tool_name="clang_sa",
    input_type="application/octet-stream",
    description="Parses plist output from the clang static analysis tool.",
    cls=ClangAnalyzerPlistParser)
