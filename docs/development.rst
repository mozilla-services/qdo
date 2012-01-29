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


Apache Kafka
============

- http://incubator.apache.org/kafka/design.html

