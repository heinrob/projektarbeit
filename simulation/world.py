
import json
import random

from location import Location
from person import Person
from wormhole import Wormhole

### container for locations, scenario loading from json files and starting point for the simulation
class World:

    
    def __init__(self, environment):
        self.environment = environment
        self.constants = dict()
        self.locations = dict()
        self.homes = dict()
        self.persons = []


    # start simulation in every warn app
    def start(self):
        for person in self.persons:
            if person.smartphone.warnApp:
                self.environment.process(person.smartphone.warnApp.start())
            self.environment.process(person.move())

    # load scenario from json file
    def load(self, filename):
        with open(filename, "r") as jsonfile:
            scenario = json.load(jsonfile)

            if 'config' in scenario:
                self.constants['packetDrop']    = scenario['config']['packetDrop']    
                self.constants['timeslots']     = scenario['config']['timeslots']    
                self.constants['scanInterval']  = scenario['config']['scanInterval']    
                self.constants['scanDuration']  = scenario['config']['scanDuration']    
                self.constants['homesickness']  = scenario['config']['homesickness']    
                self.constants['infectionRate'] = scenario['config']['infectionRate']    
                self.constants['appSaturation'] = scenario['config']['appSaturation']    

            # parse locations
            population = 0
            for location in scenario['locations']:
                if location['id'] in self.locations:
                    raise ValueError('Location ID already in use.')
                self.locations[location['id']] = Location(location, self)
                population += location['size']

            # TODO: generate people based on population. population * Person.HOMESICKNESS? -> generate Location as persons homes
            for _ in range(int(population * self.constants['homesickness'])):
                self.persons.append(Person(self))

            # parse wormholes
            for wormhole in scenario['wormholes']:
                for location in wormhole['receive']:
                    sublocation = location[1]
                    if sublocation == -1:
                        sublocation = random.randrange(0, len(self.locations[location[0]].sublocations))
                    self.locations[location[0]].wormholes[sublocation].append(Wormhole(wormhole, self))
