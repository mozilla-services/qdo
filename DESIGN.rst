Design notes
============

- one worker handles 1 to n queues
- no queue is handled by more than one worker
- worker / queue assignment is kept in zookeeper
- each worker keeps state on how far its read its queues in zookeeper
- workers get one or batches of messages from each queue
- queues are based on timestamps, workers do time range scans

- worker lifetime loop is a simple Python ``while True:``
- worker needs to check for `rebalance` request by zookeeper (triggered by
  callback function from zookeeper) - rebalance needs a lock
- zookeeper keeps persistent connection to each worker process, if connection
  goes away, worker needs to stop working / reconnect
- on worker startup, register with zookeeper, register callbacks for
  triggering rebalance (algorithm as in Kafka
  http://incubator.apache.org/kafka/design.html), zookeeper ephemeral nodes
  (with postfix -0001, -0002, ... for sorting)
- on worker shutdown, unregister with zookeeper
- fork of each actual work task (avoids leaks)

- Look for inspiration in:

    - https://github.com/bbangert/retools
    - http://celeryproject.org/

Open questions
--------------

- handle authentication / access (app token, r/w/rw privileges)
- priority queues?
- can one worker run multiple tasks at the same time? internal process pool?
  (flower / pistol)
- pause mode? without triggering rebalance (during queuey upgrades?)
- shared initial worker resources, like db connections? (context manager
  around a task with access to global state?)
- how to handle single task failure?
- max run time / mem usage on single task execution?
- execute task with lower privileges?
- guarantees on single task execution? (min 1, max 1, exact 1?)

queue / worker assignments
--------------------------

- len(queues) == len(workers): one-to-one
- len(queues) < len(workers): some workers sit idle (make sure they don't
  generate load)
- len(queues) > len(workers): some workers handle multiple queues

monitoring (metlog)
-------------------

- health check (process runs in fg mode, so process presence?)
- counter for num of processed tasks (success, failure)
- counter for zookeeper rebalance triggers
- timing info on queuey connect, task execution

command line tool
-----------------

- inspect / dump state of running worker
- pause worker?

- stats on num of queues, num of workers
- stats on num of messages (are we behind?, do we need more workers?)
