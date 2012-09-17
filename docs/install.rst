============
Installation
============

Requirements
============

Make sure you have the following software already installed before
proceeding:

- Make
- Python 2.7 (or 2.6)
- Java 1.6 (or 1.7)
- Zero MQ (zmq-dev)

Installation
============

After downloading the repository for the first time,
cd into the directory and run::

    make

This will do the following:

- Create a virtual Python environment
- Install required Python packages into this environment

If you want to use the Zookeeper based partitioner, you can also run::

    make zookeeper
