===========
Development
===========

Development of qdo takes place on github at:
https://github.com/mozilla-services/qdo

Tests
=====

Start a Queuey instance via supervisor::

    bin/supervisord

To shut it down::

    bin/supervisorctl shutdown

To run the tests call::

    make test

If you don't start supervisor yourself, `make test` will do so for you.

There's some services being started during the tests. Currently those are
hard-coded to the following ports (on 127.0.0.1):

    - 4999 Supervisor
    - 5000 Queuey

Helpers
=======

To check for new releases of all Python dependencies, run::

    bin/checkversions -i http://c.pypi.python.org/simple

or if you only want bug-fix (level 2 in 0.1.2) releases::

    bin/checkversions -l 2 -i http://c.pypi.python.org/simple

Choose a PyPi mirror that's close to you.
