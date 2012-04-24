=========
Internals
=========

Zookeeper
=========

Zookeeper is used to store information about queues, how far the queues have
been processed, available workers and what worker handles which queues.
Queues can be split into multiple partitions. We keep track of information for
each specific partition in each queue.

Data in Zookeeper is stored in a hierarchy. We use a namespace for all data,
to allow multiple applications to use the same Zookeeper cluster. This also
supports `Zookeeper partitioning
<http://wiki.apache.org/hadoop/ZooKeeper/PartitionedZookeeper>`_ as proposed
for a future Zookeeper version.

If no application specific namespace has been defined, we use:
``/mozilla-qdo/``

The Zookeeper connections use `chroot` support and connect to the specified
namespace. This ensures that the code itself can use namespace agnostic
absolute paths.

Data structure
--------------

In the following definitions ``/<qdo-ns>/`` is used as a shorthand for
``/mozilla-qdo/`` or an apps specific namespace like ``socorro-qdo``.

Workers
+++++++

Data about currently active workers is stored at::

    /<qdo-ns>/workers/

On worker connect an `ephemeral node
<http://zookeeper.apache.org/doc/current/api/org/apache/zookeeper/CreateMode.html#EPHEMERAL>`_
is created for each worker. It is automatically removed on worker disconnect.
It's name consists of the fully qualified domain name of the machine running
the worker and the worker's process id. The node has no value.

For example::

    /<qdo-ns>/workers/svc1.mozilla.com-1842
    /<qdo-ns>/workers/svc1.mozilla.com-1859
    /<qdo-ns>/workers/svc2.mozilla.com-2012

Partitions
++++++++++

Information about existing partitions is stored under::

    /<qdo-ns>/partitions/

A persistent node is created for each partition. For example::

    /<qdo-ns>/partitions/a4bb2fb6dcda4b68aad743a4746d7f58-1
    /<qdo-ns>/partitions/a4bb2fb6dcda4b68aad743a4746d7f58-2
    /<qdo-ns>/partitions/958f8c0643484f13b7fb32f27a4a2a9f-1

Each partition node stores a float value, specifying until when messages have
been processed. Messages matching the time stamp are considered processed:

.. code-block:: javascript

    '1330365230.03807'

Partition assignment
++++++++++++++++++++

The information on what worker is currently handling which partition is stored
in a third hierarchy::

    /<qdo-ns>/partition-owners/

The structure is the same as used for the partition tracking. For example::

    /<qdo-ns>/partition-owners/a4bb2fb6dcda4b68aad743a4746d7f58-1

These nodes are ephemeral nodes, constituting a lock as implemented via a
`txzookeeper.lock.Lock <http://bazaar.launchpad.net/~juju/txzookeeper/trunk/view/head:/txzookeeper/lock.py>`_.

If a re-balancing is triggered and a partition is assigned to a new worker,
the new worker will wait until it can acquire a write lock on each partition
before processing it. This ensures that no message is processed twice, both by
the old and a new worker.

Worker assignment and re-balancing
++++++++++++++++++++++++++++++++++

TODO

Email notes from Ben:

As a general outline flow for the worker, I'd imagine at start-up it functions like so:

1. Register host-pid info with ZK /workers
2. Enter 'rebalancing mode', wait until /workers node children are 'stable'
3. Obtain (and wait if needed) locks for assigned queue+partition's
4. Pull message and process it, or wait X seconds and poll again
   - In the event multiple queuey hosts were supplied, they should be divvied up to reduce how many queuey instances each worker needs to connect to. If there's 6 queuey instances, and 3 workers, each worker will be connected to just 2 queuey instances, etc. When pulling messages from multiple queuey instances, the oldest messages should be processed first.
5. Record message id that was just processed in ZK
6. Check to see if workers available has changed, go to step 2 if so
7. If workers haven't changed, go to step 4

The 'rebalancing' mode should probably hang out for several seconds, so that in
case multiple workers are being started or kiled at once, each and every
join/part doesn't cause the re-balancing itself to execute immediately, but
instead all the workers stop and wait until the children of the
/<qdo-ns>/workers node has not changed for at least 3 seconds. I.e., the
available workers has 'leveled' out. This way when someone is starting up a
bunch of workers, it'll wait 3 seconds until the last one has started up before
doing the re-balance algorithm and moving to step 3.
