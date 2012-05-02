# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import os.path
import time
import xmlrpclib

CASSANDRA = True
try:
    import pycassa
except ImportError:
    CASSANDRA = False

SUPERVISOR = True
try:
    import supervisor
    supervisor  # pyflakes
except ImportError:
    SUPERVISOR = False

from qdo import log

here = os.path.dirname(__file__)
maindir = os.path.dirname(here)
vardir = os.path.join(maindir, 'var')
processes = {}


def example_job(context, message):
    body = message[u'body']
    if body == u'stop':
        raise KeyboardInterrupt
    elif body == u'wait':
        time.sleep(0.01)


def setup_cassandra_schema():
    hosts = ['127.0.0.1:9160']
    while 1:
        try:
            pycassa.ConnectionPool(keyspace=u'MessageStore', server_list=hosts)
            break
        except pycassa.InvalidRequestException as e:
            if u'Keyspace MessageStore does not exist' in e.why:
                lhost = hosts[0].split(u':')[0]
                os.system(u'bin/cassandra/bin/cassandra-cli -host %s '
                    u'--file etc/cassandra/message_schema.txt' % lhost)
                os.system(u'bin/cassandra/bin/cassandra-cli -host %s '
                    u'--file etc/cassandra/metadata_schema.txt' % lhost)
            break
        except pycassa.AllServersUnavailable:
            time.sleep(1)


def ensure_process(name, timeout=30, noisy=True):
    srpc = processes[u'supervisor']
    if srpc.getProcessInfo(name)[u'statename'] in (u'STOPPED', u'EXITED'):
        if noisy:
            print(u'Starting %s!\n' % name)
        srpc.startProcess(name)
    # wait for startup to succeed
    for i in xrange(1, timeout):
        state = srpc.getProcessInfo(name)[u'statename']
        if state == u'RUNNING':
            break
        elif state != u'RUNNING':
            if noisy:
                print(u'Waiting on %s for %s seconds.' % (name, i * 0.1))
            time.sleep(i * 0.1)
    if srpc.getProcessInfo(name)[u'statename'] != u'RUNNING':
        for name in os.listdir(vardir):
            if name == u'README.txt':
                continue
            print(u"\n\nFILE: %s" % name)
            with open(os.path.join(vardir, name)) as f:
                print(f.read())
        raise RuntimeError(u'%s not running' % name)


def setup_supervisor():
    processes[u'supervisor'] = xmlrpclib.ServerProxy(
        u'http://127.0.0.1:4999').supervisor


def setup():
    """Shared one-time test setup, called from tests/__init__.py"""
    log.configure(None, debug=True)
    if SUPERVISOR:
        setup_supervisor()
    if CASSANDRA:
        ensure_process(u'cassandra')
        setup_cassandra_schema()
    if SUPERVISOR:
        ensure_process(u'queuey')
        ensure_process(u'nginx')


def teardown():
    """Shared one-time test tear down, called from tests/__init__.py"""
    pass
