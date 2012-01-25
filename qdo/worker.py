import time


class Worker(object):
    """A Worker works on jobs"""

    def __init__(self, settings):
        """Create a worker

        :param settings: Configuration settings
        :type settings: dict
        """
        self.settings = settings
        self.shutdown = False
        self.configure()

    def configure(self):
        """Configure the worker based on the configuration settings.
        """
        qdo_section = self.settings.getsection('qdo-worker')
        self.wait_interval = qdo_section.get('wait_interval', 5)

    def work(self):
        """Work on jobs

        This is the main method of the Worker.
        """
        while True:
            if self.shutdown:
                break
            print('Waiting %d seconds on next job.' % self.wait_interval)
            time.sleep(self.wait_interval)


def run(settings):
    worker = Worker(settings)
    worker.work()
