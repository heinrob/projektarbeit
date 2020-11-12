
import json
import random

from location import Location,Home
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

            # generate people based on population. population * Person.HOMESICKNESS? -> generate Location as persons homes
            # TODO: generate families
            target_amount = int(population * self.constants['homesickness'])
            while len(self.persons) < target_amount:
                # generate family
                family_size = random.randint(1,5)
                home = Home(self, family_size + 2) # TODO: dangerous for future
                self.homes[home.id] = home
                for _ in range(family_size):
                    self.persons.append(Person(self, home.id))

            # parse wormholes
            for wormhole in scenario['wormholes']:
                for location in wormhole['receive']:
                    sublocation = location[1]
                    if sublocation == -1:
                        sublocation = random.randrange(0, len(self.locations[location[0]].sublocations))
                    self.locations[location[0]].wormholes[sublocation].append(Wormhole(wormhole, self))
