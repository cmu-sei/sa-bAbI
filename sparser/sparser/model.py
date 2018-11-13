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
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField
from mongoengine import StringField, IntField, ListField


class ToolInfo(EmbeddedDocument):
    """Information about a static analysis tool.

    Attributes:
        name (str): name of the tool
        version(str): version string of the tool
    """
    name = StringField()
    version = StringField()


class Location(EmbeddedDocument):
    """A source code location.

    Attributes:
        path(str): a source file path
        line_start(int): the start line in the file
        line_end(int): the end line in the file
        col_start(int): the start column in the line
        col_end(int): the end column in the line
        offset(int): the file byte offset
    """
    path = StringField()
    line_start = IntField()
    line_end = IntField()
    col_start = IntField()
    col_end = IntField()
    offset = IntField()


class Message(EmbeddedDocument):
    """A static analysis tool message.

    Attributes:
        text(str): the message text 
        location: the message location
    """
    text = StringField()
    location = EmbeddedDocumentField(Location)


class Diagnostic(Document):
    """A static analysis tool diagnostic.

    Attributes:
        tool_info: information about the tool
        kind(str): The kind of diagnostic
        message: The primary message
        additional_messages: List of additional messages 
    """
    tool_info = EmbeddedDocumentField(ToolInfo)
    kind = StringField()
    message = EmbeddedDocumentField(Message)
    additional_messages = ListField(EmbeddedDocumentField(Message))
