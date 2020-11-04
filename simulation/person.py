import random


from location import Home
from smartphone import Smartphone

### movement
class Person:

    counter = 0

    def __init__(self, world):
        self.id = Person.counter
        Person.counter += 1

        self.world = world

        self.infected = random.random() <= self.world.constants['infectionRate']

        Home(self)
        self.location = self.world.homes[self.id]
        self.sublocation = 0
        self.smartphone = Smartphone(self)

        self.locationlog = []


    ### perform a movement action every now and then
    def move(self):
        while True:
            if random.random() < self.world.constants['homesickness']:
                # move home
                self.location = self.world.homes[self.id]
                self.sublocation = 0
                if len(self.locationlog) < 1 or not self.locationlog[-1] == -self.id:
                    self.locationlog.append(-self.id)
                yield self.world.environment.timeout(abs(random.gauss(self.location.stay, self.location.stayDeviation)))
            else:
                # move to a location (or another persons home?)
                # TODO smarter location selection
                for idx in random.sample(list(self.world.locations.keys()), len(self.world.locations)):
                    self.location = self.world.locations[idx]
                    if self.location.crowdiness() < random.triangular(0, 1, self.location.population):
                        #print(self.location.id, self.location.crowdiness())
                        break
                else:
                    # all locations are "full", wait a little and try again
                    #print("locations full", self.id)
                    yield self.world.environment.timeout(10)
                    continue
                self.locationlog.append(self.location.id)
                #print('moved', self.id, 'to', self.location.id)
                # move between different sublocations inside the location
                # start in sublocation 0 for a short time and end there too
                self.sublocation = self.location.moveTo(self)
                # whole duration of stay
                duration = abs(random.gauss(self.location.stay, self.location.stayDeviation))
                # amount of time already stayed, always beginning in the entry sublocation
                stay = random.triangular(0, 0.1 * duration, 0.07 * duration)
                yield self.world.environment.timeout(stay)
                while stay < duration * 0.9:
                    s = random.random() * duration
                    stay += s
                    yield self.world.environment.timeout(s)
                    self.sublocation = self.location.moveTo(self, rnd=True)
                # end in sublocation 0
                self.sublocation = self.location.moveTo(self)
                yield self.world.environment.timeout(abs(duration - stay))
                self.location.moveTo(self, -1)

    def __repr__(self):
        return str(self.id)
