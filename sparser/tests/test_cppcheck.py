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

# Copyright (c) 2007-2018 Carnegie Mellon University. All Rights Reserved.
# See COPYRIGHT file for details.

from six import BytesIO
from six import b
from yattag import Doc

from sparser import CppcheckXmlV2Parser


class TestCppchecktXmlV2Parser():
    def test_empty(self):
        doc, tag, text = Doc().tagtext()
        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag("results", version="2"):
            with tag("cppcheck", version="testVersion"):
                pass
            with tag("errors"):
                pass
        parser = CppcheckXmlV2Parser()
        results = parser.load(BytesIO(b(doc.getvalue())))
        assert len(results) == 0

    def test_one_error(self):
        doc, tag, text = Doc().tagtext()
        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag("results", version="2"):
            with tag("cppcheck", version="testVersion"):
                pass
            with tag("errors"):
                with tag("error", id="testId", verbose="testMessage"):
                    with tag(
                            "location", file="/test/file", line=1,
                            info="info"):
                        pass

        parser = CppcheckXmlV2Parser()
        results = parser.load(BytesIO(b(doc.getvalue())))
        assert len(results) == 1

        diag = results[0]
        assert diag.tool_info.name == "cppcheck"
        assert diag.tool_info.version == "testVersion"
        assert diag.kind == "testId"
        assert diag.message.location.path == "/test/file"
        assert diag.message.location.line_start == 1
        assert diag.message.text == "testMessage"

        assert len(diag.additional_messages) == 1
        message = diag.additional_messages[0]
        assert message.location.path == "/test/file"
        assert message.location.line_start == 1
        assert message.text == "info"

    def test_one_error_multiple_locs(self):
        doc, tag, text = Doc().tagtext()
        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag("results", version="2"):
            with tag("cppcheck", version="testVersion"):
                pass
            with tag("errors"):
                with tag("error", id="testId", verbose="testMessage"):
                    for i in range(10):
                        with tag(
                                "location",
                                file="/test/file" + str(i),
                                line=i,
                                info="info" + str(i)):
                            pass

        parser = CppcheckXmlV2Parser()
        results = parser.load(BytesIO(b(doc.getvalue())))
        assert len(results) == 1

        diag = results[0]
        assert diag.tool_info.name == "cppcheck"
        assert diag.tool_info.version == "testVersion"
        assert diag.kind == "testId"
        assert diag.message.location.path == "/test/file0"
        assert diag.message.location.line_start == 0
        assert diag.message.text == "testMessage"

        assert len(diag.additional_messages) == 10
        for i in range(10):
            message = diag.additional_messages[i]
            assert message.location.path == "/test/file" + str(i)
            assert message.location.line_start == i
            assert message.text == "info" + str(i)

    def test_multiple_errors(self):
        doc, tag, text = Doc().tagtext()
        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag("results", version="2"):
            with tag("cppcheck", version="testVersion"):
                pass
            with tag("errors"):
                for i in range(10):
                    with tag(
                            "error",
                            id="testId" + str(i),
                            verbose="testMessage" + str(i)):
                        with tag(
                                "location",
                                file="/test/file" + str(i),
                                line=i,
                                info="info" + str(i)):
                            pass

        parser = CppcheckXmlV2Parser()
        results = parser.load(BytesIO(b(doc.getvalue())))
        assert len(results) == 10

        for i in range(10):
            diag = results[i]
            assert diag.tool_info.name == "cppcheck"
            assert diag.tool_info.version == "testVersion"
            assert diag.kind == "testId" + str(i)
            assert diag.message.location.path == "/test/file" + str(i)
            assert diag.message.location.line_start == i
            assert diag.message.text == "testMessage" + str(i)

            assert len(diag.additional_messages) == 1
            message = diag.additional_messages[0]
            assert message.location.path == "/test/file" + str(i)
            assert message.location.line_start == i
            assert message.text == "info" + str(i)

    def test_multiple_errors_multuple_locations(self):
        doc, tag, text = Doc().tagtext()
        doc.asis('<?xml version="1.0" encoding="UTF-8"?>')
        with tag("results", version="2"):
            with tag("cppcheck", version="testVersion"):
                pass
            with tag("errors"):
                for i in range(10):
                    with tag(
                            "error",
                            id="testId" + str(i),
                            verbose="testMessage" + str(i)):
                        for j in range(10):
                            with tag(
                                    "location",
                                    file="/test/file" + str(j),
                                    line=j,
                                    info="info" + str(j)):
                                pass

        parser = CppcheckXmlV2Parser()
        results = parser.load(BytesIO(b(doc.getvalue())))
        assert len(results) == 10

        for i in range(10):
            diag = results[i]
            assert diag.tool_info.name == "cppcheck"
            assert diag.tool_info.version == "testVersion"
            assert diag.kind == "testId" + str(i)
            assert diag.message.location.path == "/test/file0"
            assert diag.message.location.line_start == 0
            assert diag.message.text == "testMessage" + str(i)
            assert len(diag.additional_messages) == 10
            for j in range(10):
                message = diag.additional_messages[j]
                assert message.location.path == "/test/file" + str(j)
                assert message.location.line_start == j
                assert message.text == "info" + str(j)
