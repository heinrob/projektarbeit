#!/usr/bin/env python3

import simpy

import random
import datetime
import argparse
import json

def getTime():
    return datetime.datetime.now().timestamp()


class Person:

    counter = 0

    def __init__(self, locationID, infected=False, appSaturation=0):
        self.id = Person.counter
        self.location = locationID
        self.infected = infected
        Person.counter += 1
        self.smartphone = Smartphone(self.location, appSaturation, self.infected)

class Smartphone:

    counter = 0

    def __init__(self, location, appSaturation, infected):
        self.id = Smartphone.counter
        Smartphone.counter += 1
        self.warnApp = None
        if random.random() <= appSaturation:
            self.warnApp = WarnApp(location, self.id, infected)


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
        day = int(environment.now/3600/24)
        timeslot = int((environment.now - day * 3600 * 24) * WarnApp.TIMESLOTS / 3600 / 24)
        rpi = f"{self.deviceID:06x}{day:06x}{timeslot:04x}"
        while True:
            # initialize scan every 5 minutes at selected timeslot
            if int(environment.now - self.scanTime) % WarnApp.SCAN_INTERVAL in range(WarnApp.SCAN_DURATION):
                #print(f"scan now {self.deviceID}: {self.scanTime}")
                ret = yield environment.process(World.locations[self.locationID].scanRPI(self.deviceID, 1))
                for entry in ret:
                    self.receivedRPIs.append(entry)
                print(self.deviceID, self.receivedRPIs)
            #print(f"{environment.now:.4f} sending RPI {rpi}")
            World.locations[self.locationID].sendRPI(rpi)
            yield environment.timeout(random.random()*0.07+0.2) # see specification
            


class Location:

    counter = 0
    PACKET_DROP = 0.2

    def __init__(self, size, population=0, infectionRate=0, appSaturation=0):
        self.id = Location.counter
        Location.counter += 1
        self.size = size
        self.population = population if population > 0 else random.random()
        self.infectionRate = infectionRate
        self.crowd = []
        
        self.generateCrowd(appSaturation)
        self.generateGroups()

        self.rpiContainer = dict()

    def generateCrowd(self, appSaturation):
        assert(self.population >= 0 and self.population <= 1)
        for _ in range(int(self.size * self.population)):
            infected = random.random() <= self.infectionRate # infection by location infection rate
            self.crowd.append(Person(self.id, infected, appSaturation))

    def generateGroups(self):
        # build mesh of contact persons
        # randomly sized intermeshed groups some single ones connected to other groups
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

        if len(self.groups) > 1:
            for _ in range((len(self.groups)+len(self.crowd))//2-1):
                # "groups of two or three" simulating single contacts
                # select two or three groups
                gr = random.sample(self.groups, random.randint(2, min(3, len(self.groups))))
                # select one person each
                self.groups.add(tuple(set([random.choice(g) for g in gr])))
        #print(self.id, self.groups)


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

    def scanRPI(self, deviceID, duration):
        self.rpiContainer[deviceID] = []
        yield environment.timeout(duration)
        return self.rpiContainer.pop(deviceID)


class World:

    locations = []

    def start(self):
        for location in World.locations:
            for person in location.crowd:
                if person.smartphone.warnApp:
                    environment.process(person.smartphone.warnApp.sendRPI())

    def load(self, filename):
        with open(filename, "r") as jsonfile:
            scenario = json.load(jsonfile)
            for location in scenario['locations']:
                World.locations.append(Location(location['size'], location['population'], location['infectionRate'], location['appSaturation']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", "-d", type=int, default=900)
    parser.add_argument("--start-time", "-t", type=float, default=getTime())
    parser.add_argument("--scenario", "-s", type=str, help="JSON scenario config file")
    args = parser.parse_args()

    environment = simpy.Environment(args.start_time)
    world = World()
    if args.scenario:
        world.load(args.scenario)
    world.start()
    environment.run(until=args.start_time+args.duration)