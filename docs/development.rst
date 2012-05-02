===========
Development
===========

Development of qdo takes place on github at:
https://github.com/mozilla-services/qdo

Tests
=====

Start Cassandra, Nginx and a Queuey instance via supervisor::

    bin/supervisord

To shut them down::

    bin/supervisorctl shutdown

To run the tests call::

    make test

If you don't start supervisor yourself, `make test` will do so for you. Note,
that the tests use the Cassandra instance and will recursively delete any
data in it as part of the test tear down.

There's a good number of services being started during the tests. Currently
those are hard-coded to the following ports (on 127.0.0.1):

    - 4999 Supervisor
    - 5000 Queuey
    - 5001-5003 Nginx
    - 7000 Cassandra
    - 9160 Cassandra

Helpers
=======

To check for new releases of all Python dependencies, run::

    bin/checkversions

or if you only want bug-fix (level 2 in 0.1.2) releases::

    bin/checkversions -l 2
