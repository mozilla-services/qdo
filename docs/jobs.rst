====
Jobs
====

qdo has a very simple job execution model. You can only configure one function
for each of the job hooks. The job function is used to process all messages in
all queues. There's currently no categorization or prioritization of messages.

Hooks
=====

There are three different hooks as configured in the configuration file.

job_context
-----------

The `job_context` points to a Python context manager and is used for one-time
setup and tear down of shared resources for all jobs. It's called at worker
startup before any job is executed and its tear down is called after the
worker has been told to shut down.

An easy way to write a context manager is using the contextlib module::

    from contextlib import contextmanager


    @contextmanager
    def job_context():
        try:
            # do some one-time setup per worker, like open DB connections
            context = {'counter': 0}
            yield context
        finally:
            # tear things down
            print('Messages processed: %s' % context['counter'])

The `job_context` function takes no arguments and yields some context object.
Since there's only one process and no threads involved in the worker itself,
you can use simple local or global data structures for the context. The
context object can be of any type, as long as the `job` hook can handle it.

job
---

The `job` hook points to a Python callable and is used to process any
message::

    def job(message, context):
        context['counter'] += 1
        print('%s: %s' % (message['message_id'], message['body']))

The callable takes two arguments. A message as returned by Queuey and the
context as setup by the `job_context` hook. A Queuey message has some common
metadata and the main `body` workload, for example::

    {
        'body': 'some data',
        'message_id': '79924e0ff10411e1850bb88d120c81de'
        'partition': 1,
        'timestamp': '1346153731.9620111',
    }

The timestamp denotes seconds since the Unix epoch in the GMT timezone.
Message ids are UUID1's.

job_failure
-----------

The `job_failure` hook is called whenever an exception is raised inside the
job hook. Only Python exceptions inheriting from `Exception` are handled.
System exceptions like `SystemExit` or `MemoryError` will cause the
job and worker to abort without calling this hook.

Messages will still be marked as processed if a failure occurred. If messages
should be retained for reprocessing, you can use the built-in
`save_failed_message` function. Either configure it directly or in addition
to some custom error handling code::

    from qdo.worker import save_failed_message


    def log_failure(message, context, queue, exc, queuey_conn):
        # retain messages for re-processing and log tracebacks
        save_failed_message(message, context, queue, exc, queuey_conn)
        # do some custom error handling
        pass

The callable takes the original message in the same format as received by the
job hook and the same job context. In addition the queue name including the
partition is provided, for example `fecafc1678cb4810b4720c41d1c29787-2`.
The `exc` argument provides the concrete Python exception that was raised by
the job hook. The `queuey_conn` argument provides access to the
`queuey_py.Client` used for retrieving messages and can be used to store
messages back into different queues like the error queues.
