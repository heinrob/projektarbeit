import random

from warnapp import WarnApp

### just contains app
class Smartphone:

    counter = 0

    def __init__(self, person):
        self.id = Smartphone.counter
        Smartphone.counter += 1
        self.owner = person
        self.warnApp = None
        if random.random() <= self.owner.world.constants['appSaturation']:
            self.warnApp = WarnApp(self)