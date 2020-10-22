#!/usr/bin/env python3

import simpy

import random
import datetime
import argparse
import json

def getTime():
    return datetime.datetime.now().timestamp()


### send rpis from $locations to $destinations
class Wormhole:
    
    def __init__(self, ID, receivers, senders):
        self.id = ID
        self.receiveFrom = receivers
        self.sendTo = senders

    # send received rpi to all connected wormhole senders
    def sendRPI(self, rpi):
        for lidx in self.sendTo:
            for device in World.locations[lidx].rpiContainer.keys():
                if random.random() > Location.PACKET_DROP: # packet drop
                    rssi = random.randint(-100, -50)
                    print("wormhole success in", lidx, rpi)
                    input()
                    World.locations[lidx].rpiContainer[device].append((environment.now, rssi, rpi))

### just contains smartphone
class Person:

    counter = 0

    def __init__(self, locationID, infected=False, appSaturation=0):
        self.id = Person.counter
        self.location = locationID
        self.infected = infected
        Person.counter += 1
        self.smartphone = Smartphone(self.location, appSaturation, self.infected)

### just contains app
class Smartphone:

    counter = 0

    def __init__(self, location, appSaturation, infected):
        self.id = Smartphone.counter
        Smartphone.counter += 1
        self.warnApp = None
        if random.random() <= appSaturation:
            self.warnApp = WarnApp(location, self.id, infected)


### mainly for sending, receiving and storing rpis
class WarnApp:

    TIMESLOTS = 144
    SCAN_INTERVAL = 5*60 # seconds
    SCAN_DURATION = 1 # seconds

    def __init__(self, location, deviceID, infected):
        self.deviceID = deviceID
        self.locationID = location
        self.infected = infected
        # randomly chosen timeslot to scan for other devices every 5 minutes
        self.scanTime = random.random() * WarnApp.SCAN_INTERVAL
        
        # save received rpis
        self.receivedRPIs = []

    def sendRPI(self):
        while True:
            # build rpi
            day = int(environment.now/3600/24)
            timeslot = int((environment.now - day * 3600 * 24) * WarnApp.TIMESLOTS / 3600 / 24)
            rpi = f"{self.deviceID:06x}{day:06x}{timeslot:04x}"

            # initialize scan every 5 minutes at selected timeslot
            if int(environment.now - self.scanTime) % WarnApp.SCAN_INTERVAL in range(WarnApp.SCAN_DURATION):
                #print(f"scan now {self.deviceID}: {self.scanTime}")
                ret = yield environment.process(World.locations[self.locationID].scanRPI(self.deviceID, 1))
                for entry in ret:
                    self.receivedRPIs.append(entry)
                print(self.deviceID, self.receivedRPIs)
            
            # send rpi to devices in range
            World.locations[self.locationID].sendRPI(rpi)
            yield environment.timeout(random.random()*0.07+0.2) # see specification
            

### contians transmission logic between apps
class Location:

    PACKET_DROP = 0.2

    def __init__(self, size, ID=-1, population=0, infectionRate=0, appSaturation=0):
        if ID > -1 and ID not in World.locations.keys():
            self.id = ID
        else:
            self.id = 0
            if len(World.locations) > 0:
                self.id = max(World.locations.keys()) + 1
        
        self.size = size
        self.population = population if population > 0 else random.random()
        self.infectionRate = infectionRate
        self.crowd = []
        
        self.generateCrowd(appSaturation)
        self.generateGroups()

        self.rpiContainer = dict()
        self.wormholes = []

    # fill location with people
    def generateCrowd(self, appSaturation):
        assert(self.population >= 0 and self.population <= 1)
        for _ in range(int(self.size * self.population)):
            infected = random.random() <= self.infectionRate # infection by location infection rate
            self.crowd.append(Person(self.id, infected, appSaturation))

    def generateGroups(self):
        # build mesh of contact persons
        # randomly sized intermeshed groups, some single persons connected to other groups
        self.groups = set()
        crowdIds = [p.id for p in self.crowd]
        ungrouped = crowdIds[:]
        random.shuffle(ungrouped)
        while True:
            # group size: 2 - 10
            splitpoint = random.randint(2,10)
            group = ungrouped[0:splitpoint]
            self.groups.add(tuple(set(group)))
            ungrouped = ungrouped[splitpoint:]
            if len(ungrouped) < 10:
                if len(ungrouped) > 0:
                    self.groups.add(tuple(set(ungrouped)))
                break
        
        # create single contacts inbetween groups
        if len(self.groups) > 1:
            for _ in range((len(self.groups)+len(self.crowd))//2-1):
                # "groups of two or three" simulating single contacts
                # select two or three groups
                gr = random.sample(self.groups, random.randint(2, min(3, len(self.groups))))
                # select one person each
                self.groups.add(tuple(set([random.choice(g) for g in gr])))


    # check if both persons are in one group
    def isContact(self, deviceID, rpi):
        deviceB = int(rpi[:6], base=16)
        for group in self.groups:
            if deviceID in group and deviceB in group:
                return True
        return False


    def sendRPI(self, rpi):
        for device in self.rpiContainer.keys():
            if self.isContact(device, rpi):
                if random.random() > Location.PACKET_DROP: # packet drop
                    rssi = random.randint(-100, -50)
                    self.rpiContainer[device].append((environment.now, rssi, rpi))
        ### wormholes
        for wormhole in self.wormholes:
            print("sending to", wormhole.sendTo)
            wormhole.sendRPI(rpi)

    # start scanning, open a container and receive for $duration time, returns the container
    def scanRPI(self, deviceID, duration):
        self.rpiContainer[deviceID] = []
        yield environment.timeout(duration)
        return self.rpiContainer.pop(deviceID)


### container for locations, scenario loading from json files and starting point for the simulation
class World:

    locations = dict()

    # start simulation in every warn app
    def start(self):
        for lidx in World.locations:
            for person in World.locations[lidx].crowd:
                if person.smartphone.warnApp:
                    environment.process(person.smartphone.warnApp.sendRPI())

    # load scenario from json file
    def load(self, filename):
        with open(filename, "r") as jsonfile:
            scenario = json.load(jsonfile)

            # parse locations
            for location in scenario['locations']:
                if location['id'] not in World.locations:
                    ID = location['id']
                else:
                    ID = max(World.locations.keys()) + 1
                World.locations[ID] = Location(location['size'], ID, location['population'], location['infectionRate'], location['appSaturation'])

            # parse wormholes
            for wormhole in scenario['wormholes']:
                for location in wormhole['receive']:
                    World.locations[location].wormholes.append(Wormhole(wormhole['id'], wormhole['receive'], wormhole['send']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", "-d", type=int, default=900)
    parser.add_argument("--start-time", "-t", type=float, default=getTime())
    parser.add_argument("--scenario", "-s", type=str, help="JSON scenario config file")
    args = parser.parse_args()

    # set up the environmet
    environment = simpy.Environment(args.start_time)
    world = World()
    if args.scenario:
        world.load(args.scenario)
    
    # start simulation
    world.start()
    environment.run(until=args.start_time+args.duration)