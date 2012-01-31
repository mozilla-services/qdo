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

Each worker node stores a JSON value, specifying which queues it is
currently handling:

.. code-block:: javascript

    '{"queues": []}'

For example:

.. code-block:: javascript

    '{"queues":
      ["a4bb2fb6dcda4b68aad743a4746d7f58",
       "958f8c0643484f13b7fb32f27a4a2a9f"]}'

TODO: Explain watchers for re-balancing.

Queues
++++++

Information about existing queues is stored under::

    /<qdo-ns>/queues/

A persistent node is created for each queue. For example::

    /<qdo-ns>/queues/a4bb2fb6dcda4b68aad743a4746d7f58
    /<qdo-ns>/queues/958f8c0643484f13b7fb32f27a4a2a9f

Each queue node stores a JSON value, specifying until what time messages
have been processed:

.. code-block:: javascript

    '{"last": ""}'

If no message has been processed yet, an empty string is stored.

For example:

.. code-block:: javascript

    '{"last": "135471512647131000L"}'
