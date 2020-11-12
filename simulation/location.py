import math
import random

#from world import World


### contians transmission logic between apps
class Location:


    def __init__(self, location_js, world):
        self.id = location_js['id']
        self.size = location_js['size']
        self.population = location_js['population']
        self.stay = location_js['stay']
        self.stayDeviation = location_js['deviation']

        self.world = world



        ### TODO sublocations max(math.log(self.size), 1)
        number_sublocations = max(int((math.log(self.size) + math.sqrt(self.size)) / 2), 1)
        self.sublocations = {x: [] for x in range(number_sublocations)}
        # self.rpiContainer = {x: dict() for x in range(len(self.sublocations))}
        self.receivers = {x: [] for x in range(number_sublocations)}
        self.wormholes = {x: [] for x in range(number_sublocations)}
        #print(self.rpiContainer)


    def sendRPI(self, rpi, sublocation):
        for receiver in self.receivers[sublocation]:
            if random.random() > self.world.constants['packetDrop']: # packet drop
                rssi = random.randint(-100, -50)
                receiver.receiveRPI(self.world.environment.now, rssi, rpi)
        ### wormholes
        for wormhole in self.wormholes[sublocation]:
            wormhole.sendRPI(rpi)

    # start scanning, open a container and receive for $duration time, returns the container
    def scanRPI(self, receiver, sublocation):
        if receiver in self.receivers[sublocation]:
            return
        self.receivers[sublocation].append(receiver)
        yield self.world.environment.timeout(self.world.constants['scanDuration'])
        self.receivers[sublocation].remove(receiver)

    # move person between sublocations, -1 removes person from location
    def moveTo(self, person, destination=0, rnd=False):
        for l in self.sublocations:
            if person in self.sublocations[l]:
                self.sublocations[l].remove(person)
                break
        if rnd:
            if len(self.sublocations) > 1:
                destination = random.randrange(1, len(self.sublocations))
        if destination > -1:
            self.sublocations[destination].append(person)
            #print("moved person", person.id, "to", destination, "in", self.id)
            #print(self.id, self.sublocations)
        return destination

    def crowdiness(self):
        return sum([len(self.sublocations[x]) for x in self.sublocations]) / self.size


class Home(Location):

    counter = 0

    def __init__(self, world, size):
        super().__init__({"id": Home.counter, "size": size, "population": 1, "stay": 720, "deviation": 300}, world)
        Home.counter += 1

        #inhabitant.world.homes[self.id] = self

    def moveTo(self, person, destination=0, rnd=False):
        super().moveTo(person, destination, False)
