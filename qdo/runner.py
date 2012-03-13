# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import os.path
import sys

import pkg_resources
from mozsvc.config import load_into_settings

from qdo import worker
from qdo.config import QdoSettings
from qdo.utils import configure_metlog

DEFAULT_CONFIGFILE = os.path.join(os.curdir, 'etc', 'qdo-worker.conf')


def _nicepath(filename):
    filename = os.path.abspath(os.path.normpath(os.path.expandvars(
        os.path.expanduser(filename))))
    if os.path.isfile(filename):
        return filename
    return None


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
    filename = _nicepath(filename)
    if filename is None:
        return None
    # side effect, populates settings dictionary
    config = load_into_settings(filename, settings)
    # handle ca_bundle
    ca_bundle = settings['qdo-worker.ca_bundle']
    if ca_bundle:
        ca_bundle = _nicepath(ca_bundle)
        if ca_bundle is not None:
            os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
    configure_metlog(settings.getsection('metlog'))
    return config


def run(args=sys.argv[1:]):
    arguments = parse_args(args)
    settings = QdoSettings()
    config = parse_config(arguments.configfile, settings)
    if config is None:
        print('Configuration file not found or cannot be read.')
        sys.exit(1)
    worker.run(settings)  # pragma: no cover
    sys.exit(0)  # pragma: no cover
