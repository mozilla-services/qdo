================================================================
qdo: Python worker library for Mozilla Services' message queuing
================================================================

qdo
    pronounced `qu-doe`

This is a worker library implemented in Python used for processing
queued messages from a :term:`Mozilla Services` message queue. More soon, in
the meantime, you can read the
`specification <https://wiki.mozilla.org/Services/Sagrada/Queuey>`_ on the
Mozilla wiki or look at the message queue implementation called
:term:`Queuey` itself.

Quick intro
===========

Assuming you have a working installation and setup of Queuey and Zookeeper,
you need at least one Python module named `hello.py`::

    from contextlib import contextmanager


    @contextmanager
    def job_context():
        try:
            # do some one-time setup per worker, like open DB connections
            context = {u'counter': 0}
            yield context
        finally:
            # tear things down
            print(u'Messages processed: ', context[u'counter'])


    def job(context, message):
        context[u'counter'] += 1
        print(message[u'body'])

And one config file named `hello.conf`:

.. code-block:: ini

    [qdo-worker]
    context = hello:job_context
    job = hello:job

    [zookeeper]
    connection = 127.0.0.1:2181
    namespace = hello

    [queuey]
    connection = https://127.0.0.1:5000/v1/queuey/
    app_key = f25bfb8fe200475c8a0532a9cbe7651e

Then run::

   bin/qdo-worker -c hello.conf


Contents
========

.. toctree::
   :maxdepth: 2

   install
   config
   api
   logging
   development
   internals
   changelog

Index and Glossary
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`search`

.. toctree::
   :hidden:

   glossary
