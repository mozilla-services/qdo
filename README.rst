================================================================
qdo: Python worker library for Mozilla Services' message queuing
================================================================

This is a Python implementation of a worker library used for processing
queued messages from a MozSvc message queue. More soon, in the meantime,
you can read the `spec <https://wiki.mozilla.org/Services/MessageQueuing>`_
on the Mozilla wiki or look at the message queue implementation called
`Queuey <https://github.com/mozilla-services/queuey>`_ itself.


.. note:: This code is not yet stable. Please contact
          `Hanno Schlichting <hschlichting@mozilla.com>`_ if you are
          interested.

Requirements
============

Make sure you have the following software already installed before
proceeding:

- Make
- Python 2.6 (with virtualenv installed, available as `virtualenv-2.6`)

Installation
============

After downloading the repository for the first time,
cd into the directory and run make.

This will do the following:

- Create a virtual Python environment
- Install required Python packages into this environment

Development
===========

Run the tests via::

    make test
