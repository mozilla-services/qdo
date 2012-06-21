TODO
====

worker
------

- use time uuids instead of timestamps for progress tracking
- increase default status/error partitions to 7

- use 'admin/status' queue
- add 'storage policy'
- add instructions for consumer-dev environment, with memory-based queuey
  and no nginx nor ssl
- rewrite/update internals.txt
- add job error handling hook / use 'failed' queue

queuey
------

- implement smarter fallback on Queuey connections, not just try-once
- add nicer error handling, wrap non-2xx responses and JSON parsing problems
  in exceptions and print out response text as part of the exception /
  traceback

future
------

- look over design.rst - integrate into docs
- add build rpm structure
