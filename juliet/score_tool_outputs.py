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
import re
import yaml
import json
import csv
import logging
from pathlib import PurePath
from collections import defaultdict, namedtuple
import xml.etree.ElementTree as ET

Alert = namedtuple('Alert', ["tool", "checker", "file", "line", "message"])


def correlate(alerts, defects):
    return ((a, get_tag_for_alert(a, defects)) for a in alerts)


def follows_rule(rule, s):
    return \
        (type(rule) is str and rule == s) \
     or (type(rule) is dict and ("regex" in rule and re.match(rule["regex"], s)))


def is_whitelisted(alert, whitelist):
    rules = whitelist.get(alert.tool) or {}
    checker_rules = rules.get("checkers") or []
    message_rules = rules.get("messages") or []
    return \
        any((follows_rule(rule, alert.checker) for rule in checker_rules)) \
     or any((follows_rule(rule, alert.message) for rule in message_rules))


def load_alerts(alerts_path, whitelist):
    result = []
    with open(alerts_path, "r") as fid:
        for alert in csv.reader(fid):
            try:
                alert_obj = Alert._make(alert)
            except:
                continue
            if is_whitelisted(alert_obj, whitelist):
                result.append(alert_obj)
    return result


def get_flaws(manifest_file, cwes):
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    flaws = defaultdict(list)
    for testcase in root.iter("testcase"):
        for testfile in testcase.iter("file"):
            name = testfile.get("path")
            if name.endswith(".cpp"):
                continue

            for flaw in testfile.iter("flaw"):
                cwe_str = flaw.get("name").split(":")[0]
                cwe = int(cwe_str.replace("CWE-", "").lstrip("0"))
                if cwe in cwes:
                    line = int(flaw.get("line"))
                    flaws[name].append(line)
    return flaws


def load_checker_whitelist(whitelist_path):
    with open(whitelist_path, "r") as fid:
        data = yaml.load(fid)
    return data


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("whitelist")
    parser.add_argument("alert_files", nargs="+")
    parser.add_argument(
        '-v',
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING)

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    cwes = set([121])
    flaws = get_flaws(args.manifest, cwes)
    whitelist = load_checker_whitelist(args.whitelist)

    alerts = []
    for alert_file in args.alert_files:
        alerts += load_alerts(alert_file, whitelist)

    all_tools = set([a.tool for a in alerts])
    alert_index = defaultdict(list)
    for alert in alerts:
        alert_index[(PurePath(alert.file).name, int(alert.line))].append(alert)

    flaw_scores = {
        # For each tool
        tool: {
            # True indicates a positive response
            True: 0,
            # False indicates a negative reponse
            False: 0
        }
        for tool in all_tools
    }

    seen = set()
    for filename, lines in flaws.items():
        for line in lines:
            seen.add((filename, line))
            hits = alert_index[(filename, line)]
            tools = set([h.tool for h in hits])

            for tool in tools:
                # Indicate a positive response
                flaw_scores[tool][True] += 1
                logging.debug("RESPONSE,%s,%s,%d", tool, filename, line)
            for other in (all_tools - tools):
                # Indicate a negative response
                flaw_scores[other][False] += 1
                logging.debug("NO_RESPONSE,%s,%s,%d", other, filename, line)

    false_positives = defaultdict(int)

    for alert in alerts:
        location = (PurePath(alert.file).name, int(alert.line))
        if location not in seen:
            false_positives[alert.tool] += 1

    writer = csv.writer(sys.stdout)
    writer.writerow(["tool", "tp", "fn", "fp"])
    for tool in all_tools:
        writer.writerow([
            tool, flaw_scores[tool][True], flaw_scores[tool][False],
            false_positives[tool]
        ])
