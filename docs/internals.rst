=========
Internals
=========

Zookeeper
=========

Zookeeper is used to store information about queues, how far the queues have
been processed, available workers and what worker handles which queues.

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
``/mozilla-qdo/`` or an apps specific namespace like `socorro-qdo`.

Workers
+++++++

Data about currently active workers is stored at::

    /<qdo-ns>/workers/

On worker connect an `ephemeral node
<http://zookeeper.apache.org/doc/current/api/org/apache/zookeeper/CreateMode.html#EPHEMERAL>`_
is created for each worker. It is automatically removed on worker disconnect.
It's name consists of the fully qualified domain name of the machine running
the worker and the workers process id.

For example::

    /<qdo-ns>/workers/svc1.mozilla.com-1842
    /<qdo-ns>/workers/svc1.mozilla.com-1859
    /<qdo-ns>/workers/svc2.mozilla.com-2012

Each worker node stores a JSON value, specifying which queue partitions it is
currently handling:

.. code-block:: javascript

    '{"queues": []}'

For example:

.. code-block:: javascript

    '{"queues":
      ["a4bb2fb6dcda4b68aad743a4746d7f58-1",
       "958f8c0643484f13b7fb32f27a4a2a9f-2"]}'

Queues
++++++

Information about existing queues is stored under::

    /<qdo-ns>/queues/

A persistent node is created for each queue id / partition combination. For
example::

    /<qdo-ns>/queues/a4bb2fb6dcda4b68aad743a4746d7f58-1
    /<qdo-ns>/queues/a4bb2fb6dcda4b68aad743a4746d7f58-2
    /<qdo-ns>/queues/958f8c0643484f13b7fb32f27a4a2a9f-1

Each queue node stores a JSON value, specifying until when messages have been
processed:

.. code-block:: javascript

    '{"last": ""}'

If no message has been processed yet, an empty string is stored.

For example:

.. code-block:: javascript

    '{"last": "135471512647131000L"}'

Queue assignment
++++++++++++++++

The information on what worker is currently handling which queue is stored in
a third hierarchy::

    /<qdo-ns>/queue-locks/

The structure is the same as used for the queue tracking. For example::

    /<qdo-ns>/queue-locks/a4bb2fb6dcda4b68aad743a4746d7f58-1

These nodes are ephemeral nodes, constituting a lock as implemented via a
`zktools.locking.ZkWriteLock <http://zktools.readthedocs.org/en/latest/api/locking.html>`_.

If a rebalancing happens and a queue is assigned to a new worker, the new worker
will wait until it can acquire a write lock on each queue before processing it.
This ensures that no message is processed twice, both by the old and a new
worker.

Worker queue assignment and rebalancing
+++++++++++++++++++++++++++++++++++++++

TODO
