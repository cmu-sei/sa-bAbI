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
import xml.etree.ElementTree as ET
from .model import Diagnostic, Message, Location, ToolInfo
from .parser import Parser, register_parser


class CppcheckXmlV2Parser(Parser):
    """A parser for the cppcheck v2 XML format

    This class parsers alerts from version 2 of the XML format produced
    by the tool cppcheck. Alerts in this format have the following general
    shape::

        <error id="checkerName"
               severity="error"
                msg="Error message."
               verbose="Verbose error message."
               cwe="CWE Number">
            <location file="foo.c" line="17" info="Message 1"/>
            <location file="foo.c" line="13" info="Message 2"/>
        </error>

    We interpret the "verbose" attribute as the primary message, and the
    "info" attributes of the location nodes to be additional messages.
    However, the line number and file name from the first location
    are used as the location for the primary message, since no location
    is otherwise specified in the attributes of the error.

    The recommended command line invocation of cppcheck is::

        cppcheck --xml --enable-all 2> output.xml

    "output.xml" then can be consumed by this parser.
    """

    def load_iter(self, input_file):
        """Generates diagnostics from the Cppcheck v2 XML format

        Args:
            input_file (binary file-like object): A binary file-like object 
            containing Cppcheck v2 XML.

        Returns:
            An iterator of Diagnostic objects
        """

        tree = ET.parse(input_file)
        root = tree.getroot()

        cppcheck_node = root.find("cppcheck")
        version = cppcheck_node.get("version")
        tool_info = ToolInfo(name="cppcheck", version=version)

        for error_node in root.iter("error"):
            diag = Diagnostic(tool_info=tool_info, kind=error_node.get("id"))

            messages = [
                Message(
                    text=node.get("info"),
                    location=Location(
                        path=node.get("file"),
                        line_start=int(node.get("line"))))
                for node in error_node.findall("location")
            ]
            diag.additional_messages = messages
            diag.message = Message(text=error_node.get("verbose"))
            if len(messages) > 0:
                # Steal the location from the first location nodem if it exists
                diag.message.location = messages[0].location

            yield diag


register_parser(
    name="cppcheck_xml",
    tool_name="cppcheck",
    input_type="application/xml",
    description="Parses xml output (v2) from cppcheck.",
    cls=CppcheckXmlV2Parser)
