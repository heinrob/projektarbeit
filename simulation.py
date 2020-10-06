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

    def __init__(self, size, population=0, infectionRate=0, appSaturation=0):
        self.id = Location.counter
        Location.counter += 1
        self.size = size
        self.infectionRate = infectionRate
        self.crowd = []
        if population == 0:
            self.generateCrowd(random.random(), appSaturation)
        else:
            self.generateCrowd(population, appSaturation)

        self.rpiContainer = dict()

    def generateCrowd(self, population, appSaturation):
        assert(population >= 0 and population <= 1)
        for _ in range(int(self.size * population)):
            infected = random.random() <= self.infectionRate # infection by location infection rate
            self.crowd.append(Person(self.id, infected, appSaturation))

    def sendRPI(self, rpi):
        for device in self.rpiContainer.keys():
            self.rpiContainer[device].append((environment.now, rpi))

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