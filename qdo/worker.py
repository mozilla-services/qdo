import time
from pprint import pprint


class Worker(object):
    """A Worker works on jobs"""

    def __init__(self, settings):
        """Create a worker

        :param settings: Configuration settings
        :type settings: dict
        """
        self.shutdown = False

    def work(self, interval=5):
        """Work on jobs

        This is the main method of the Worker.

        :param interval: Time in seconds between polling.
        :type interval: int
        """
        while True:
            if self.shutdown:
                break
            print('Waiting %d seconds on next job.' % interval)
            time.sleep(interval)


def run(settings):
    pprint(settings)
    worker = Worker(settings)
    worker.work()
