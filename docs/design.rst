============
Design notes
============

qdo tries to keep things simple and robust. Some features are intentionally
left out, like process management, memory or CPU limitations as there's
dedicated external tools like `circus <http://circus.readthedocs.org>`_ or
`supervisord <http://supervisord.org/>`_ for these tasks.

There's also no process or thread pools implemented inside qdo. Scaling qdo
is done via starting multiple qdo worker scripts. Qdo can automatically
discover all queues in Queuey and coordinate queue to worker assignment using
:term:`Zookeeper`, so starting new worker instances is automatic and painless.

All actual persistent data is stored inside Queuey (Cassandra) including
information on task completion. If Zookeeper is used, it only stores volatile
data about the current configuration of the cluster. But if the entire cluster
is shut down, all data inside Zookeeper can be removed and will be recreated
when the cluster is started up again.

All parts of Queuey and qdo are optimized for a cluster setup of at least
three nodes for each component. It's possible to use a single instance
setup for development purposes though. This is reflected in all parts
supporting configuration of multiple back-end nodes and random selection
of nodes and automatic fail-over amongst nodes. It's assumed that the exact
same on-disk configuration files will be used for configuring multiple nodes
(as they are likely put in place by tools like Puppet or Chef). The entire
system can transparently handle reconfiguration and re-balancing in case a
minority of nodes of any part goes down.

One qdo worker process handles zero up to many partitions of queues at the
same time. One specific partition is only ever handled by one worker.
This exact assignment is either handled manually via configuration files or
is ensured by using distributed locks backed by :term:`Zookeeper`.

Monitoring (:term:`metlog`)
---------------------------

qdo uses :term:`Mozilla Services` :term:`metlog` libraries to provide logging
and metrics gathering. No logging or metric data is kept on local machines,
but all data is sent to dedicated logging and metric services.
