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
- fork of each actual work task (avoids leaks, TODO: measure overhead)

- Look for inspiration in:

    - https://github.com/bbangert/retools
    - http://celeryproject.org/

Open questions
--------------

- handle authentication / access (app token, r/w/rw privileges)
- priority queues?

  - Let user running worker declare multiple queues, queues are queried in order
    for messages to provide priority (highest priority should be first)
- can one worker run multiple tasks at the same time? internal process pool?
  (flower / pistol)

  - Nope
- what happens if the worker task itself uses async i/o / greenlets or
  multiple threads?

  - Shouldn't matter to the qdo
- pause mode? without triggering rebalance (during queuey upgrades?)

  - Perhaps, not in initial version. If queuey goes down, worker should stay alive
    and wait for it to come back
- shared initial worker resources, like db connections? (context manager
  around a task with access to global state?)

  - Yes, user should be able to provide a 'on-startup' hook that will be executed at
    worker startup before forking
- how to handle single task failure? skip and log or stop?

  - Two options should be available, log errors, and queue failures. If 'queue failures'
    then failed messages should be put on a queuey failure queue (so they can be easily
    retried later if desired)
- max run time / mem usage on single task execution?

  - Not in initial version, later updates should have configurable run-time/mem usage.
- execute task with lower privileges?

  - This currently is a trusted model where the user the worker executes as is already
    the lowest privilege desired, so not needed.
- guarantees on single task execution? (min 1, max 1, exact 1?)

  - When logging every successful message process to Zookeeper, this guarantee should be
    implicit.
- do we need any special handling for startup? like 10 workers coming online
  in a short period of time? should this trigger 10 rebalance requests?
  same with shutdown of multiple workers at once

  - Probably not important, rebalancing should be a fairly cheap operation, will have
    to revisit once we can test.

queue main loop
---------------

- fetch new messages from queue (can this be done async/greenlety?)
- cache messages per queue
- for each message, execute task (os.fork)
- record completion in zookeeper (after single message or after batch?)
- select next message or next queue (when handling multiple queues)

questions
+++++++++

- when working with multiple queues, handle one batch of messages per queue
  first or take one message from each queue each?

  - Handle one message per queue, in order. This provides priority. If a user
    wants to process more messages from the same queue at once then more
    workers should be spawned.
- on rebalancing, evict local message cache or try to revalidate / keep
  messages for queues still handled by the worker

  - Remove local message cache so that the worker can release the queue+parititon
    as soon as possible in case it no longer owns the queue+partition after the
    rebalance
- should there be a batch task mode, where a task can optionally handle
  multiple messages at once? maybe more effecient to write results out to
  target systems. when to record task success / handle failures?

  - Not at first, maybe later. the Python requests lib has HTTP 1.1 keep-alive now
    which makes repeat requests cheap. So it's quite likely the pain of pulling
    multiple messages at once isn't worth it, yet. If the message can be processed
    very very quickly, such that throughput is a concern, this should be revisited.

queue / worker assignments
--------------------------

- len(queues*partitions) == len(workers): one-to-one
- len(queues*partitions) < len(workers): some workers sit idle (make sure they don't
  generate load)
- len(queues*partitions) > len(workers): some workers handle multiple queues and/or
  multiple partitions for the same queue

monitoring (metlog)
-------------------

- health check (process runs in fg mode, so process presence?)

  - Looking at zookeeper should also reveal health, as dead processes will lose their
    session state in zookeeper, and cause a rebalance, logging the rebalance should
    help diagnose issues in health.
- counter for num of processed tasks (success, failure)
- counter for zookeeper rebalance triggers
- timing info on queuey connect, task execution

command line tool
-----------------

- inspect / dump state of running worker (via SIGUSRx signals?)
- pause worker?

- stats on num of queues, num of workers
- stats on num of messages (are we behind?, do we need more workers?)

signals
-------

- sighup: reload config? not at first -> just restart
- sigint: graceful stop, complete current task
- sigusr1: reopen log files -> reopen metlog connection?
- sigusr2: maybe dump state / statistics to stdout?
- sigterm: abort task, but close connection to zookeeper
- sigkill: die!
- sigalarm: maybe handle time limits on tasks via signals.alarm()
