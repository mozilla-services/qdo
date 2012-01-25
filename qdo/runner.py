# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import os.path
import sys

import pkg_resources
from mozsvc.config import load_into_settings, SettingsDict

from qdo import worker

DEFAULT_CONFIGFILE = os.path.join(os.curdir, 'etc', 'qdo-worker.conf')


def parse_args(args):
    version = pkg_resources.get_distribution('qdo').version
    parser = argparse.ArgumentParser(description='qdo worker')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('-c', '--config', action='store',
                        dest='configfile', default=DEFAULT_CONFIGFILE,
                        help='specify configuration file, defaults to '
                             '%s' % DEFAULT_CONFIGFILE)
    return parser.parse_args(args=args)


def parse_config(filename, settings):
    filename = os.path.abspath(os.path.normpath(os.path.expandvars(
        os.path.expanduser(filename))))
    if not os.path.isfile(filename):
        return None
    # side effect, populates settings dictionary
    return load_into_settings(filename, settings)


def run():
    args = parse_args(sys.argv[1:])
    settings = SettingsDict()
    config = parse_config(args.configfile, settings)
    if config is None:
        print('Configuration file not found or cannot be read.')
        sys.exit(1)
    worker.run(settings)
    sys.exit(0)
