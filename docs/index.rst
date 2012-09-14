================================================================
qdo: Python worker library for Mozilla Services' message queuing
================================================================

qdo
    pronounced `qu-doe`

This is a Python implementation of a worker library used for processing
queued messages from a :term:`Mozilla Services` message queue. The message
queue is called `Queuey <https://github.com/mozilla-services/queuey>`_ and is
implemented as a :term:`Pyramid` based web service on top of :term:`Cassandra`.

Quick intro
===========

Assuming you have a working installation and setup of :term:`Queuey`,
you need at least one Python module, for example `hello.py`::

    from contextlib import contextmanager


    @contextmanager
    def job_context():
        try:
            # do some one-time setup per worker, like open DB connections
            context = {'counter': 0}
            yield context
        finally:
            # tear things down
            print('Messages processed: %s' % context['counter'])


    def job(message, context):
        context['counter'] += 1
        print('%s: %s' % (message['message_id'], message['body']))

And one config file named `hello.conf`:

.. code-block:: ini

    [qdo-worker]
    job = hello:job
    job_context = hello:job_context

    [queuey]
    connection = http://127.0.0.1:5000/v1/queuey/,http://127.0.0.1:5001/v1/queuey/
    app_key = f25bfb8fe200475c8a0532a9cbe7651e

Then run:

.. code-block:: sh

   $ bin/qdo-worker -c hello.conf


Contents
========

.. toctree::
   :maxdepth: 2

   install
   config
   jobs
   logging
   api
   design
   development
   changelog

Index and Glossary
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`search`

.. toctree::
   :hidden:

   glossary
