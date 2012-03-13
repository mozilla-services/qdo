TODO
====

queue
-----

- How to handle multiple queues? Only some partitions of one queue?

utils
-----

- Make metlog sender configurable via ini file

worker
------

- add `get queues` hook (dotted path to function via ini file - get ZK and
  Queuey connection as arguments?)
- define `job` API

zookeeper
---------

- factor zookeeper handling out of worker
- implement event handling / queue distribution

general
-------

- Be explicit about unicode / bytes
- change zktools node last_modified time to use the ZK time instead of local
  process time

future
------

- look over design.rst - integrate into docs
- reduce direct qdo dependencies (no pyramid please)
- add back prod-reqs.txt / build rpm structure
- implement smarter fallback on Queuey connections, not just try-once
