=========
Zookeeper
=========

Zookeeper can be used to store information about available workers and what
worker handles which queues.

Data structure
--------------

Worker
++++++

Data about currently active workers is stored at::

    /worker/

On worker connect an `ephemeral node
<http://zookeeper.apache.org/doc/current/api/org/apache/zookeeper/CreateMode.html#EPHEMERAL>`_
is created for each worker. It is automatically removed on worker disconnect.
It's name consists of the fully qualified domain name of the machine running
the worker and the worker's process id. The node has no value.

For example::

    /worker/svc1.mozilla.com-1842
    /worker/svc1.mozilla.com-1859
    /worker/svc2.mozilla.com-2012

Worker assignment
+++++++++++++++++

The information on what worker is currently handling which queue partition is
managed by the `kazoo SetPartitioner recipe <http://kazoo.readthedocs.org/en/latest/api/recipe/partitioner.html>`_
The data is stored under the `assignment` node::

    /assignment/
