===========
Development
===========

Here's a list of useful docs and descriptions of some of the parts qdo is
based on:

Zookeeper
=========

Links
+++++

- http://zktools.readthedocs.org/en/latest/index.html
- http://zookeeper.apache.org/doc/current/zookeeperProgrammers.html
- http://zookeeper.apache.org/doc/current/api/index.html?org/apache/zookeeper/ZooKeeper.html
- http://svn.apache.org/repos/asf/zookeeper/trunk/src/contrib/zkpython/src/test/

Inspect Zookeeper
-----------------

After starting Zookeeper, use the command line client::

    $ bin/zookeeper/bin/zkCli.sh
    Connecting to localhost:2181
    ...
    WATCHER::

    WatchedEvent state:SyncConnected type:None path:null
    [zk: localhost:2181(CONNECTED) 0]

    [zk:] ls /
    [zookeeper]

    [zk:] get /
    cZxid = 0x0
    ctime = Thu Jan 01 01:00:00 CET 1970
    mZxid = 0x0
    mtime = Thu Jan 01 01:00:00 CET 1970
    pZxid = 0xea
    cversion = 37
    dataVersion = 0
    aclVersion = 0
    ephemeralOwner = 0x0
    dataLength = 0
    numChildren = 2

    [zk:] help
    connect host:port
    get path [watch]
    ls path [watch]
    set path data [version]
    ...
    setquota -n|-b val path

    [zk:] quit

Zookeeper internals
-------------------

A single node in Zookeeper should contain at most 1MB of data and a single
response from Zookeeper is by default restricted to the same amount. There's
no direct restriction on how many children one node can contain, but reports
on the mailing lists suggest scaling to 10,000 to 100,000 can work.

Zookeeper stores a number of different data structures. The main one is the
`DataTree <http://svn.apache.org/viewvc/zookeeper/tags/release-3.4.2/src/java/main/org/apache/zookeeper/server/DataTree.java?revision=1225684&view=markup>`_
This keeps a `java.util.concurrent.ConcurrentHashMap
<http://docs.oracle.com/javase/6/docs/api/java/util/concurrent/ConcurrentHashMap.html>`_
containing the full path to a node to the actual DataNode itself::

    ConcurrentHashMap<String, DataNode> nodes =
        new ConcurrentHashMap<String, DataNode>();

Java's string object defines a `hashCode
<http://docs.oracle.com/javase/6/docs/api/java/lang/String.html#hashCode%28%29>`_
as::

    s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]

where s[i] is the ith character of the string and n is the length of the
string.

Each data node stores a pointer to its parent and a list of strings for all
its children (relative path), the number of children it has and a bunch of
extra metadata like version number and timestamps. One node without any extra
data consumes between 40 and 80 bytes of runtime memory.

Almost all data access happens through the hash map, so length of sub-paths is
not important. The only exception is serialization to disk, which traverses
the tree starting from the root node, recursively down into all children, but
gets the data nodes again via the hash map.

Apache Kafka
============

- http://incubator.apache.org/kafka/design.html
