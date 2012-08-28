===================
Logging and metrics
===================

qdo uses :term:`metlog` libraries for logging of events and metrics.

Metrics
=======

Counter
-------

The following metrics are sent as incrementing counter events.

worker.wait_for_jobs
    Sent when a worker has no more messages to process and sits idle. Sent
    once per configured wait period.

Exceptions
----------

By default failed jobs will be logged and skipped. The job failure will be
logged using `metlog-raven` including a full Python traceback.

Timer
-----

The following metrics are sent as timing data.

worker.job_time
    Time for a job to process a single message.

worker.job_failure_time
    Time to process each job failure.
