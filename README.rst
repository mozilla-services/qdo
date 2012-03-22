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
- Java 1.6
- Zero MQ (zmq-dev)
- libevent-dev, libpcre-dev

Installation
============

After downloading the repository for the first time,
cd into the directory and run::

    make

This will do the following:

- Create a virtual Python environment
- Install required Python packages into this environment
- Install Cassandra, Nginx and Zookeeper

If you get a problem installing gevent on Mac OS, make sure you have libevent
installed and retry installation::

    export CFLAGS=-I/opt/local/include
    export LDFLAGS=-L/opt/local/lib
    bin/pip install gevent
