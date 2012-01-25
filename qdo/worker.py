# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import sys

import pkg_resources
from mozsvc.config import load_into_settings, SettingsDict


def parse_args():
    version = pkg_resources.get_distribution('qdo').version
    parser = argparse.ArgumentParser(description='qdo worker')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('configfile', action='store',
                        help='specify configuration file')
    return parser.parse_args()


def parse_config(filename, settings):
    filename = os.path.abspath(os.path.normpath(os.path.expandvars(
        os.path.expanduser(filename))))
    if not os.path.isfile(filename):
        return None
    # side effect, populates settings dictionary
    return load_into_settings(filename, settings)


def work():
    args = parse_args()
    settings = SettingsDict()
    config = parse_config(args.configfile, settings)
    if config is None:
        print('Configuration file not found or cannot be read.')
        sys.exit(1)
    from pprint import pprint
    pprint(settings)
    sys.exit(0)
