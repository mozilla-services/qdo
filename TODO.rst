TODO
====

worker
------

- add `get queues` hook (dotted path to function via ini file - get ZK and
  Queuey connection as arguments?)

zookeeper
---------

- factor zookeeper handling out of worker
- implement event handling / queue distribution

future
------

- look over design.rst - integrate into docs
- reduce direct qdo dependencies (no pyramid please)
- add back prod-reqs.txt / build rpm structure
- implement smarter fallback on Queuey connections, not just try-once
