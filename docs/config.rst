=============
Configuration
=============

`qdo` uses an ini-style configuration file for most of its configuration. The
configuration file is specified via the `-c` option to the `qdo-worker`
script. It defaults to `etc/qdo-worker.conf`.

For example::

    bin/qdo-worker -c etc/my-qdo.conf

Settings
========

Settings are organized into multiple sections.

[qdo-worker]
------------

wait_interval
    Interval in seconds for which the worker pauses if it has no messages to
    work on. Defaults to 5 seconds.

[queuey]
--------

connection
    Which :term:`Queuey` instance(s) to connect to. Defaults to
    `https://127.0.0.1:5001/v1/queuey/`. Multiple instances can be specified
    as a comma separated list: `https://127.0.0.1:5001/v1/queuey/,https://127.0.0.1:5002/v1/queuey/`

app_key
    The application key used for authorization.

[zookeeper]
-----------

connection
    Which :term:`Zookeeper` instance(s) to connect to. Defaults to
    `127.0.0.1:2181`. Multiple :term:`Zookeeper` instances can be specified
    as a comma separated list: 10.0.0.1:2181,10.0.0.2:2181,10.0.0.3:2181

namespace
    The path to the root :term:`Zookeeper` node, under which `qdo` will store
    all its information. Defaults to `mozilla-qdo`. The node needs to be
    created before `qdo-worker` is run.
