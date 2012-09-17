# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import os.path
import time
import xmlrpclib

from qdo import log
from qdo.worker import StopWorker

here = os.path.dirname(__file__)
maindir = os.path.dirname(here)
vardir = os.path.join(maindir, 'var')
processes = {}


def example_job(message, context):
    body = message['body']
    if body == 'stop':
        raise StopWorker
    elif body == 'wait':
        time.sleep(0.01)


def ensure_process(name, timeout=30, noisy=True):
    srpc = processes['supervisor']
    if srpc.getProcessInfo(name)['statename'] in ('STOPPED', 'EXITED'):
        if noisy:
            print('Starting %s!\n' % name)
        srpc.startProcess(name)
    # wait for startup to succeed
    for i in xrange(1, timeout):
        state = srpc.getProcessInfo(name)['statename']
        if state == 'RUNNING':
            break
        elif state != 'RUNNING':
            if noisy:
                print('Waiting on %s for %s seconds.' % (name, i * 0.1))
            time.sleep(i * 0.1)
    if srpc.getProcessInfo(name)['statename'] != 'RUNNING':
        for name in os.listdir(vardir):
            if name == 'README.txt':
                continue
            print('\n\nFILE: %s' % name)
            with open(os.path.join(vardir, name)) as f:
                print(f.read())
        raise RuntimeError('%s not running' % name)


def setup_supervisor():
    processes['supervisor'] = xmlrpclib.ServerProxy(
        'http://127.0.0.1:4999').supervisor


def setup():
    """Shared one-time test setup, called from tests/__init__.py"""
    log.configure(None, debug=True)
    setup_supervisor()
    ensure_process('queuey')


def teardown():
    """Shared one-time test tear down, called from tests/__init__.py"""
    pass
