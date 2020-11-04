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
        self.rpiContainer = {x: dict() for x in range(len(self.sublocations))}
        self.wormholes = {x: [] for x in range(number_sublocations)}
        #print(self.rpiContainer)


    def sendRPI(self, rpi, sublocation):
        for device in self.rpiContainer[sublocation].keys():
            # if self.isContact(device, rpi):
            if random.random() > self.world.constants['packetDrop']: # packet drop
                rssi = random.randint(-100, -50)
                self.rpiContainer[sublocation][device].append((self.world.environment.now, rssi, rpi))
        ### wormholes
        for wormhole in self.wormholes[sublocation]:
            #print("sending to", wormhole.sendTo)
            wormhole.sendRPI(rpi)

    # start scanning, open a container and receive for $duration time, returns the container
    def scanRPI(self, deviceID, sublocation):
        self.rpiContainer[sublocation][deviceID] = []
        yield self.world.environment.timeout(self.world.constants['scanDuration'])
        return self.rpiContainer[sublocation].pop(deviceID)

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
    def __init__(self, inhabitant):
        super().__init__({"id": inhabitant.id, "size": 5, "population": 1.0/5.0, "stay": 720, "deviation": 300}, inhabitant.world)

        inhabitant.world.homes[self.id] = self

    def moveTo(self, person, destination=0, rnd=False):
        super().moveTo(person, destination, False)
