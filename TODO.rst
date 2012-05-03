TODO
====

worker
------

- use 'admin/status' queue
- add 'storage policy'
- add instructions for consumer-dev environment, with memory-based queuey
  and no nginx nor ssl
- rewrite/update internals.txt
- add job error handling hook / use 'failed' queue

queuey
------

- implement smarter fallback on Queuey connections, not just try-once

future
------

- smart host selection for queuey (prefer localhost), instead of random
- look over design.rst - integrate into docs
- add build rpm structure
