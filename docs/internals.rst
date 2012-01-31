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

The namespace used for qdo is: ``/mozilla/services/qdo/``

TODO: Use namespace / chroot support as noted in
http://zookeeper.apache.org/doc/r3.2.2/zookeeperProgrammers.html#ch_zkSessions
"Added in 3.2.0: An optional "chroot" suffix may also be appended to the
connection string. This will run the client commands while interpreting all
paths relative to this root (similar to the unix chroot command)"


Data structure
--------------

In the following definitions ``/<qdo-ns>/`` is used as a shorthand for
``/mozilla/services/qdo/``.

Applications
++++++++++++

qdo supports multiple applications at the same time or at least coordinating
them in the same Zookeeper instance.

Each application has an unique app name, as defined by
https://wiki.mozilla.org/Services/Sagrada/TokenServer.

From here on ``<app_name>`` is used as a shorthand for this application name.
It might for example be `sync`.

Workers
+++++++

Data about currently active workers is stored at::

    /<qdo-ns>/<app_name>/workers/

On worker connect an `ephemeral and sequential node
<http://zookeeper.apache.org/doc/current/api/org/apache/zookeeper/CreateMode.html#EPHEMERAL_SEQUENTIAL>`_
is created for each worker. It is automatically removed on worker disconnect.
Numbers in the sequence are never reused, so after some time the numbers will
be getting larger. With worker disconnects happening out of order, there's
also likely holes in the sequence.

For example::

    /<qdo-ns>/<app_name>/workers/worker-0000000101
    /<qdo-ns>/<app_name>/workers/worker-0000000105
    /<qdo-ns>/<app_name>/workers/worker-0000000106

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

    /<qdo-ns>/<app_name>/queues/

A persistent node is created for each queue. For example::

    /<qdo-ns>/<app_name>/queues/a4bb2fb6dcda4b68aad743a4746d7f58
    /<qdo-ns>/<app_name>/queues/958f8c0643484f13b7fb32f27a4a2a9f

Each queue node stores a JSON value, specifying until what time messages
have been processed:

.. code-block:: javascript

    '{"last": ""}'

If no message has been processed yet, an empty string is stored.

For example:

.. code-block:: javascript

    '{"last": "135471512647131000L"}'
