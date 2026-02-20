# Autoloop module for SWARMZ runtime

import time

class AutoLoop:
    def __init__(self, interval):
        self.interval = interval
        self.running = False

    def start(self):
        self.running = True
        while self.running:
            print("AutoLoop tick")
            time.sleep(self.interval)

    def stop(self):
        self.running = False