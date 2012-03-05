================================================================
qdo: Python worker library for Mozilla Services' message queuing
================================================================

qdo
    pronounced `qu-doe`

This is a Python implementation of a worker library used for processing
queued messages from a MozSvc message queue. More soon, in the meantime,
you can read the `spec <https://wiki.mozilla.org/Services/Sagrada/Queuey>`_
on the Mozilla wiki or look at the message queue implementation called
`Queuey <https://github.com/mozilla-services/queuey>`_ itself.


.. note:: This code is not yet stable. Please contact
          `Hanno Schlichting <hschlichting@mozilla.com>`_ if you are
          interested.

Documentation
=============

You can read the documentation at http://qdo.readthedocs.org/

Requirements
============

Make sure you have the following software already installed before
proceeding:

- Make
- Python 2.6 (with virtualenv installed, available as `virtualenv-2.6`)
- Zero MQ (zmq)
- libevent

Installation
============

After downloading the repository for the first time,
cd into the directory and run make.

This will do the following:

- Create a virtual Python environment
- Install required Python packages into this environment

Afterwards install Cassandra, Nginx and Zookeeper::

    make cassandra
    make nginx
    make zookeeper

Start Cassandra once in foreground mode and install the schema::

    ./bin/cassandra/bin/cassandra -f
    ./bin/cassandra/bin/cassandra-cli -host localhost --file etc/cassandra/message_schema.txt
    ./bin/cassandra/bin/cassandra-cli -host localhost --file etc/cassandra/metadata_schema.txt

If you get a problem installing gevent on Mac OS, make sure you have libevent
installed and retry installation::

    export CFLAGS=-I/opt/local/include
    export LDFLAGS=-L/opt/local/lib
    bin/pip install gevent

Development
===========

Start Cassandra, Nginx, Zookeeper and a Queuey instance via supervisor::

    bin/supervisord

To shut them down::

    bin/supervisorctl shutdown

To run the tests call::

    make test

This will start and stop supervisord. You can start supervisord yourself,
in which case it won't be stopped at the end of the test run. Do this if you
want to run the tests multiple times. Also note, that the tests use the
Cassandra and Zookeeper instances and will recursively delete any data in them
as part of the test tear down.
