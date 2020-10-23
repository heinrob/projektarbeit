#!/usr/bin/env python3

import simpy

import random
import datetime
import argparse
import json
import math

def getTime():
    return datetime.datetime.now().timestamp()


### send rpis from $locations to $destinations
class Wormhole:
    
    def __init__(self, wormhole_js):
        self.id = wormhole_js['id']
        self.receiveFrom = wormhole_js['receive']
        self.sendTo = wormhole_js['send']
        for entry in range(len(self.sendTo)):
            if self.sendTo[entry][1] == -1:
                self.sendTo[entry][1] = random.randrange(0, len(World.locations[self.sendTo[entry][0]].sublocations))

    # send received rpi to all connected wormhole senders
    def sendRPI(self, rpi):
        for lidx, sublocation in self.sendTo:
            for device in World.locations[lidx].rpiContainer[sublocation].keys():
                if random.random() > Location.PACKET_DROP: # packet drop
                    rssi = random.randint(-100, -50)
                    #print("wormhole success in", lidx, rpi)
                    #input()
                    World.locations[lidx].rpiContainer[sublocation][device].append((environment.now, rssi, rpi))

### just contains smartphone
class Person:

    HOMESICKNESS = 0.8
    INFECTION_RATE = 0.001
    counter = 0

    def __init__(self):
        self.id = Person.counter
        Person.counter += 1
        self.infected = random.random() <= Person.INFECTION_RATE

        Home(self)
        self.location = World.homes[self.id]
        self.sublocation = 0
        self.smartphone = Smartphone(self)

        self.locationlog = []


    ### perform a movement action every now and then
    def move(self):
        while True:
            if random.random() < Person.HOMESICKNESS:
                # move home
                self.location = World.homes[self.id]
                self.sublocation = 0
                if len(self.locationlog) < 1 or not self.locationlog[-1] == -self.id:
                    self.locationlog.append(-self.id)
                yield environment.timeout(abs(random.gauss(self.location.stay, self.location.stayDeviation)))
            else:
                # move to a location (or another persons home?)
                # TODO smarter location selection
                for idx in random.sample(list(World.locations.keys()), len(World.locations)):
                    self.location = World.locations[idx]
                    if self.location.crowdiness() < random.triangular(0, 1, self.location.population):
                        #print(self.location.id, self.location.crowdiness())
                        break
                else:
                    # all locations are "full", wait a little and try again
                    #print("locations full", self.id)
                    yield environment.timeout(10)
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
                yield environment.timeout(stay)
                while stay < duration * 0.9:
                    s = random.random() * duration
                    stay += s
                    yield environment.timeout(s)
                    self.sublocation = self.location.moveTo(self, rnd=True)
                # end in sublocation 0
                self.sublocation = self.location.moveTo(self)
                yield environment.timeout(abs(duration - stay))
                self.location.moveTo(self, -1)

    def __repr__(self):
        return str(self.id)



### just contains app
class Smartphone:

    APP_SATURATION = 0.6
    counter = 0

    def __init__(self, person):
        self.id = Smartphone.counter
        Smartphone.counter += 1
        self.owner = person
        self.warnApp = None
        if random.random() <= Smartphone.APP_SATURATION:
            self.warnApp = WarnApp(self)


### mainly for sending, receiving and storing rpis
class WarnApp:

    TIMESLOTS = 144
    SCAN_INTERVAL = 5*60 # seconds
    SCAN_DURATION = 1 # seconds

    def __init__(self, smartphone):
        self.device = smartphone
        # randomly chosen timeslot to scan for other devices every 5 minutes
        self.scanTime = random.random() * WarnApp.SCAN_INTERVAL
        
        # save received rpis
        self.receivedRPIs = []

    def start(self):
        while True:
            # build rpi
            day = int(environment.now/3600/24)
            timeslot = int((environment.now - day * 3600 * 24) * WarnApp.TIMESLOTS / 3600 / 24)
            rpi = f"{self.device.id:06x}{day:06x}{timeslot:04x}"

            # initialize scan every 5 minutes at selected timeslot
            if int(environment.now - self.scanTime) % WarnApp.SCAN_INTERVAL in range(WarnApp.SCAN_DURATION):
                #print(f"scan now {self.deviceID}: {self.scanTime}")
                ret = yield environment.process(self.device.owner.location.scanRPI(self.device.id, self.device.owner.sublocation))
                for entry in ret:
                    self.receivedRPIs.append(entry)
            
            # send rpi to devices in range
            self.device.owner.location.sendRPI(rpi, self.device.owner.sublocation)
            #print(f"send {self.device.owner.location.id}: {rpi}")
            yield environment.timeout(random.random()*0.07+0.2) # see specification





### contians transmission logic between apps
class Location:

    PACKET_DROP = 0.2

    def __init__(self, location_js):
        self.id = location_js['id']
        self.size = location_js['size']
        self.population = location_js['population']
        self.stay = location_js['stay']
        self.stayDeviation = location_js['deviation']


        # self.wormholes = []

        ### TODO sublocations max(math.log(self.size), 1)
        number_sublocations = max(int((math.log(self.size) + math.sqrt(self.size)) / 2), 1)
        self.sublocations = {x: [] for x in range(number_sublocations)}
        self.rpiContainer = {x: dict() for x in range(len(self.sublocations))}
        self.wormholes = {x: [] for x in range(number_sublocations)}
        #print(self.rpiContainer)


    def sendRPI(self, rpi, sublocation):
        for device in self.rpiContainer[sublocation].keys():
            # if self.isContact(device, rpi):
            if random.random() > Location.PACKET_DROP: # packet drop
                rssi = random.randint(-100, -50)
                self.rpiContainer[sublocation][device].append((environment.now, rssi, rpi))
        ### wormholes
        for wormhole in self.wormholes[sublocation]:
            #print("sending to", wormhole.sendTo)
            wormhole.sendRPI(rpi)

    # start scanning, open a container and receive for $duration time, returns the container
    def scanRPI(self, deviceID, sublocation):
        self.rpiContainer[sublocation][deviceID] = []
        yield environment.timeout(WarnApp.SCAN_DURATION)
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
        super().__init__({"id": inhabitant.id, "size": 5, "population": 1.0/5.0, "stay": 720, "deviation": 300})

        World.homes[self.id] = self

    def moveTo(self, person, destination=0, rnd=False):
        super().moveTo(person, destination, False)


### container for locations, scenario loading from json files and starting point for the simulation
class World:

    locations = dict()
    homes = dict()
    persons = []

    # start simulation in every warn app
    def start(self):
        for person in World.persons:
            if person.smartphone.warnApp:
                environment.process(person.smartphone.warnApp.start())
            environment.process(person.move())

    # load scenario from json file
    def load(self, filename):
        with open(filename, "r") as jsonfile:
            scenario = json.load(jsonfile)

            if 'config' in scenario:
                Location.PACKET_DROP = scenario['config']['packetDrop']
                WarnApp.TIMESLOTS = scenario['config']['timeslots']
                WarnApp.SCAN_INTERVAL = scenario['config']['scanInterval']
                WarnApp.SCAN_DURATION = scenario['config']['scanDuration']
                Person.HOMESICKNESS = scenario['config']['homesickness']
                Person.INFECTION_RATE = scenario['config']['infectionRate']
                Smartphone.APP_SATURATION = scenario['config']['appSaturation']

            # parse locations
            population = 0
            for location in scenario['locations']:
                if location['id'] in World.locations:
                    raise ValueError('Location ID already in use.')
                World.locations[location['id']] = Location(location)
                population += location['size']

            # TODO: generate people based on population. population * Person.HOMESICKNESS? -> generate Location as persons homes
            for _ in range(int(population * Person.HOMESICKNESS)):
                World.persons.append(Person())

            # parse wormholes
            for wormhole in scenario['wormholes']:
                for location in wormhole['receive']:
                    sublocation = location[1]
                    if sublocation == -1:
                        sublocation = random.randrange(0, len(World.locations[location[0]].sublocations))
                    World.locations[location[0]].wormholes[sublocation].append(Wormhole(wormhole))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", type=str, help="JSON scenario config file")
    parser.add_argument("--duration", "-d", type=int, default=3600)
    parser.add_argument("--start-time", "-t", type=float, default=getTime())
    args = parser.parse_args()

    # set up the environmet
    environment = simpy.Environment(args.start_time)
    world = World()
    world.load(args.scenario)
    
    # start simulation
    world.start()
    environment.run(until=args.start_time+args.duration)

    for person in World.persons:
        print(person.id, person.locationlog)
        #input()
print()
print('location log for each person, negative IDs indicate home')