=============
Configuration
=============

`qdo` uses an ini-style configuration file for its configuration. The
configuration file is specified via the `-c` option to the `qdo-worker`
script. It defaults to `etc/qdo-worker.conf`.

For example::

    bin/qdo-worker -c etc/my-qdo.conf

Settings
========

Settings are organized into multiple sections.

[qdo-worker]
------------

job
    The :term:`resource specification` for the Python job function. For
    example: `qdo.testing:example_job`

job_context
    The :term:`resource specification` for a Python job context (manager).
    For example: `qdo.worker:dict_context`

ca_bundle
    Path to a private certificate used for SSL connections, in addition to all
    officially signed ones.

wait_interval
    Interval in seconds for which the worker pauses if it has no messages to
    work on. Defaults to 5 seconds.

[partitions]
------------

policy
    Specifies how to get all partition ids for this worker. Defaults to
    `manual`, in which case an explicit list of `ids` has to be specified.
    The other value is `all`, which gets a list of all partitions from
    Queuey and assigns them to this worker.

status_queue
    The uuid of a special queue used for tracking the processing status for
    all other queues. This queue must not contain normal messages.

error_queue
    The uuid of a special queue used for tracking failed jobs for
    all other queues. This queue must not contain normal messages.

ids
    Only used when the policy is `manual`. A new-line separated list of
    partitions, for example::

        ids =
            a4bb2fb6dcda4b68aad743a4746d7f58-1
            a4bb2fb6dcda4b68aad743a4746d7f58-2
            958f8c0643484f13b7fb32f27a4a2a9f-1

[queuey]
--------

connection
    Which :term:`Queuey` instance(s) to connect to. Defaults to
    `https://127.0.0.1:5001/v1/queuey/`. Multiple instances can be specified
    as a comma separated list: `https://127.0.0.1:5001/v1/queuey/,https://127.0.0.1:5002/v1/queuey/`. With multiple servers, one will be selected at random
    and the others will serve as transparent fallback.

app_key
    The application key used for authorization.
