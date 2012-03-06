===================
Logging and metrics
===================

qdo uses :term:`metlog` libraries for logging of events and metrics.

Metrics
=======

Counter
-------

The following metrics are sent as incrementing counter events.

queuey.conn_error
    Sent when there's a connection error reaching the :term:`Queuey` server.

queuey.conn_ssl_error
    Sent when there's a SSL error reaching the :term:`Queuey` server.

queuey.conn_timeout
    Sent when the connection to the :term:`Queuey` server times out.

worker.wait_for_jobs
    Sent when a worker has no more messages to process and sits idle. Sent
    once per configured `wait_interval`.

Timer
-----

The following metrics are sent as timing data.

queuey.get_queues
    Time for each request getting the list of all queues and partitions.

queuey.get_messages
    Time for each request getting any number of messages.

zookeeper.get_value
    Time to read a :term:`Zookeeper` node value.

zookeeper.set_value
    Time to set a new :term:`Zookeeper` node value.
