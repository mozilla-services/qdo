================================================================
qdo: Python worker library for Mozilla Services' message queuing
================================================================

.. image:: https://secure.travis-ci.org/mozilla-services/qdo.png?branch=master
   :width: 82px
   :height: 13px
   :alt: Travis CI build report
   :target: https://secure.travis-ci.org/#!/mozilla-services/qdo

qdo
    pronounced `qu-doe`

This is a Python implementation of a worker library used for processing
queued messages from a Mozilla Services message queue. The message queue is
called `Queuey <https://github.com/mozilla-services/queuey>`_ and is
implemented as a :term:`Pyramid` based web service on top of :term:`Cassandra`.


.. note:: This code is still a bit experimental. Please contact
          `Hanno Schlichting <hschlichting@mozilla.com>`_ if you have any
          questions.

Documentation
=============

You can read the documentation at http://qdo.readthedocs.org/
