============
Installation
============

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
- Install Cassandra and Nginx

If you get a problem installing gevent on Mac OS, make sure you have libevent
installed and retry installation::

    export CFLAGS=-I/opt/local/include
    export LDFLAGS=-L/opt/local/lib
    bin/pip install gevent
