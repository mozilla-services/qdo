.. _queuey_module:

:mod:`qdo.queuey`
--------------------

Contains :term:`Queuey` connection. The connection automatically handles
retries on connection timeouts and fall back to alternate :term:`Queuey`
servers on SSL or connection errors. Currently fall back happens exactly once
per server until the worker process is restarted.

.. automodule:: qdo.queuey

Classes
~~~~~~~

.. autoclass:: QueueyConnection
    :members:
    :inherited-members:

Functions
~~~~~~~~~

.. autofunction:: retry

.. autofunction:: fallback
