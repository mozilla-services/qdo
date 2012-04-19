TODO
====

worker
------

- add `get queues` hook (dotted path to function via ini file - get ZK and
  Queuey connection as arguments?)

queuey
------

- implement smarter fallback on Queuey connections, not just try-once

zookeeper
---------

- factor zookeeper handling out of worker
- implement event handling / queue distribution

future
------

- smart host selection for queuey and zookeeper (prefer localhost), instead
  of random
- look over design.rst - integrate into docs
- reduce direct qdo dependencies (no pyramid please)
- add back prod-reqs.txt / build rpm structure
