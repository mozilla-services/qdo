===================
Logging and metrics
===================

qdo uses Mozilla's `metlog <https://github.com/mozilla-services/metlog-py>`_
libraries for logging of events and metrics.

Metrics
=======

The following metrics are sent as incrementing counter events.

queuey.conn_timeout
    Sent when the connection to the Queuey server times out.

worker.wait_for_jobs
    Sent when a worker has no more messages to process and sits idle.
