from time import sleep, time


class Retarder:
    def __init__(self, delay):
        self.next = 0
        self.delay = delay

    def step(self):
        delta = self.next - time()
        if delta > 0:
            sleep(delta)
        self.next = time() + self.delay
