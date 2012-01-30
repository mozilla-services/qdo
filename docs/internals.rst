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

TODO: Does storing queues in a single node scale? What about notifications
and potentially millions of queues? Should we implement a tree structure,
and do we know how queue ids (`uuid.uuid4().hex`) are distributed?

Some discussions in:

http://mail-archives.apache.org/mod_mbox/hadoop-zookeeper-user/200901.mbox/%3CC5922217.169DF%25mahadev@yahoo-inc.com%3E
https://issues.apache.org/jira/browse/ZOOKEEPER-272
https://issues.apache.org/jira/browse/ZOOKEEPER-1162

These seem to suggest a single znode should only have about 1mb of data and a
single response (like getChildren) should only be 1mb each. In the mail thread
it's suggested to implement a Trie for dealing with more nodes.

Zookeeper stores a number of different data structures. The main one is the
DataTree (http://svn.apache.org/viewvc/zookeeper/tags/release-3.4.2/src/java/main/org/apache/zookeeper/server/DataTree.java?revision=1225684&view=markup)
This keeps a `java.util.concurrent.ConcurrentHashMap
<http://docs.oracle.com/javase/6/docs/api/java/util/concurrent/ConcurrentHashMap.html>`_
containing the full path to a node to the actual DataNode itself::

    ConcurrentHashMap<String, DataNode> nodes =
        new ConcurrentHashMap<String, DataNode>();

Java's string object defines a `hashCode
<http://docs.oracle.com/javase/6/docs/api/java/lang/String.html#hashCode%28%29>`_
as::

    s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]

where s[i] is the ith character of the string and n is the length of the string

Each data node stores a pointer to its parent and a list of strings for all
its children (relative path) as well as the number of children it has.

Almost all data access happens through the hash map, so length of sub-paths is
not important. The only exception is serialization to disk, which traverses
the tree starting from the root node, recursively down into all children, but
gets the data nodes again via the hash map.
