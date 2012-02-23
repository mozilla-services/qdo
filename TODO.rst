TODO
====

queue
-----

- Add support for specifying multiple Queuey hosts and connect to a different
  one one connection problems
- Verify connection pool and `consume / preload body` on head requests

- How to handle multiple queues? Only some partitions of one queue?
- Add SSL handling

utils
-----

- Make metlog sender configurable via ini file

worker
------

- rewrite test_worker tests to use real queuey data
- add `get queues` hook (dotted path to function via ini file - get ZK and
  Queuey connection as arguments?)
- define `job` API

zookeeper
---------

- factor zookeeper handling out of worker
- ensure / document how fail-over to multiple hosts works
- implement event handling / queue distribution

future
------

- look over design.rst - integrate into docs
- reduce direct qdo dependencies (no pyramid please)
- add back prod-reqs.txt / build rpm structure
