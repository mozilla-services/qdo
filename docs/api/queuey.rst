.. _queuey_module:

:mod:`qdo.queuey`
--------------------

Contains a :term:`Queuey` connection helper.

The connection automatically handles retries on connection timeouts and fall
back to alternate :term:`Queuey` servers on SSL or connection errors.
Currently fall back happens exactly once per server, after which it is
considered inactive. You have to restart the worker process to reset the
inactive status.

The connection uses a connection pool as provided by the
`requests <http://docs.python-requests.org>`_ library and turns on keep alive
connections by default. SSL is supported by default and certificates will be
checked for validity. If you want to use a private certificate, you can use the
`REQUESTS_CA_BUNDLE <http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification>`_
environment variable and note the full file system path to your certificate.

.. automodule:: qdo.queuey

Classes
~~~~~~~

.. autoclass:: QueueyConnection

    .. automethod:: connect()
    .. automethod:: get(url='', params=None)
    .. automethod:: post(url='', params=None, data='')
    .. automethod:: delete(url='', params=None)

Functions
~~~~~~~~~

.. py:decorator:: retry

   On connection timeouts, retry the action.

.. py:decorator:: fallback

   On connection errors, fall back to alternate servers.
