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
from six import BytesIO
from six import b
from sparser import FramacWarningParser


def get_framac_warning(path="path", line=1, module="module", text="text"):
    fmt = "{0}:{1}:[{2}] warning: {3}\n"
    return fmt.format(path, line, module, text)


class TestFramacWarningParser():
    def test_empty(self):
        warnings = ""
        parser = FramacWarningParser()
        results = parser.load(BytesIO(b(warnings)))
        assert len(results) == 0

    def test_one_error(self):
        warnings = get_framac_warning(
            path="/test/path", line=1, module="module", text="testtext")
        parser = FramacWarningParser()
        results = parser.load(BytesIO(b(warnings)))
        assert len(results) == 1
        diag = results[0]

        assert diag.tool_info.name == "frama-c"
        assert diag.kind == "module"
        assert diag.message.location.path == "/test/path"
        assert diag.message.location.line_start == 1
        assert diag.message.text == "testtext"
        assert diag.additional_messages == []

    def test_multiple_diags(self):
        warnings = "".join([
            get_framac_warning(
                path="/test/path" + str(i),
                line=i,
                module="module" + str(i),
                text="testtext" + str(i)) for i in range(10)
        ])
        parser = FramacWarningParser()
        results = parser.load(BytesIO(b(warnings)))
        assert len(results) == 10

        for i in range(10):
            diag = results[i]
            assert diag.tool_info.name == "frama-c"
            assert diag.kind == "module" + str(i)
            assert diag.message.location.path == "/test/path" + str(i)
            assert diag.message.location.line_start == i
            assert diag.message.text == "testtext" + str(i)
            assert diag.additional_messages == []
