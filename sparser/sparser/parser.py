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
import abc
import six
import logging
from collections import namedtuple

Registry = dict()
ParserInfo = namedtuple(
    'ParserInfo', ["name", "tool_name", "input_type", "description", "cls"])


def register_parser(name, tool_name, input_type, description, cls):
    if name in Registry:
        msg = "Attempting to register parser with name '{0}', ".format(name)
        msg += "but this name is already registered."
        raise ValueError(msg)

    info = ParserInfo(
        name=name,
        tool_name=tool_name,
        input_type=input_type,
        description=description,
        cls=cls)
    Registry[name] = info

@six.add_metaclass(abc.ABCMeta)
class Parser():
    def load(self, file_obj):
        return list(self.load_iter(file_obj))

    @abc.abstractmethod
    def load_iter(self, file_obj):
        pass


def parser_entrypoint():
    import sys
    import argparse
    import mongoengine
    import csv

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("parser_name", choices=Registry.keys(), metavar="parser_name")
    arg_parser.add_argument("input_files", nargs="+")
    arg_parser.add_argument("--tool_version")
    arg_parser.add_argument("--mongo_uri")
    arg_parser.add_argument(
        '-v',
        '--verbose',
        help="Be verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args = arg_parser.parse_args()

    # NOTE: If args.loglevel is None, basicConfig will use the
    # default log level of "WARNING"
    logging.basicConfig(
        level=args.loglevel, format="%(levelname)s: %(message)s")
    logger = logging.getLogger('sparser_main')

    write_to_mongo = False
    if args.mongo_uri is not None:
        mongoengine.connect(host=args.mongo_uri)
        write_to_mongo = True

    parser_info = Registry.get(args.parser_name)
    if parser_info is None:
        logger.error("Could not find a parser named: '%s'", args.parser_name)
        logger.error("Valid parser names are as follows:")
        for key in Registry:
            logger.error("\t- " + key)
        sys.exit(1)
    csv_writer = csv.writer(sys.stdout)
    parser_instance = parser_info.cls()
    for item in args.input_files:
        with open(item, 'rb') as input_file:
            for alert in parser_instance.load_iter(input_file):
                if alert.message.location is None:
                    continue

                if args.tool_version is not None:
                    alert.tool_version_string = args.tool_version
                if write_to_mongo:
                    alert.save()
                else:
                    csv_writer.writerow([
                        alert.tool_info.name, 
                        alert.kind, 
                        alert.message.location.path,
                        alert.message.location.line_start,
                        alert.message.text])
