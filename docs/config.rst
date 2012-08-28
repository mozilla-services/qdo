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
    Defaults to: `qdo.worker:dict_context`

job_failure
    The :term:`resource specification` for a Python exception handler. The
    default is `qdo.worker:log_failure`, which logs full tracebacks of job
    failures using `metlog-raven`. Another built-in alternative is
    `qdo.worker:save_failed_message`, which logs in the same way, but also
    copies the failed message to an error queue for later inspection.

ca_bundle
    Path to a private certificate used for SSL connections, in addition to all
    officially signed ones.

wait_interval
    Interval in seconds for which the worker pauses if it has no messages to
    work on. Defaults to 30 seconds. The actual wait time adds some jitter
    of 20%, to avoid multiple workers hitting the Queuey back-end at exactly
    the same times.

[partitions]
------------

policy
    Specifies how to get all partition ids for this worker. Defaults to
    `manual`, in which case an explicit list of `ids` has to be specified.
    The other value is `all`, which gets a list of all partitions from
    Queuey and assigns them to this worker.

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
    `http://127.0.0.1:5000/v1/queuey/`. Multiple instances can be specified
    as a comma separated list: `https://127.0.0.1:5001/v1/queuey/,https://localhost:5002/v1/queuey/`.

    If multiple servers are specified, one will be selected as default and
    the others serve as transparent fallback options. The selection prefers a
    local server (127.0.0.*, localhost or ::1) and chooses at random amongst
    multiple other candidates.

app_key
    The application key used for authorization.


[metlog]
--------

For detailed information see the
`metlog docs <http://metlog-py.readthedocs.org/en/latest/config.html>`_.

qdo uses the standard metlog configuration for timing and counter data. In
addition you can configure the `metlog_plugin_raven` section, if you want to
get full tracebacks logged for job failures.
