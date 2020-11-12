#!/usr/bin/env python3

import argparse
import simpy
import datetime


from world import World

def getTime():
    return datetime.datetime.now().timestamp()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", type=str, help="JSON scenario config file")
    parser.add_argument("--duration", "-d", type=int, default=3600)
    parser.add_argument("--start-time", "-t", type=float, default=getTime())
    args = parser.parse_args()

    # set up the environmet
    environment = simpy.Environment(args.start_time)
    world = World(environment)
    world.load(args.scenario)
    
    # start simulation
    world.start()
    environment.run(until=args.start_time+args.duration)

    for person in world.persons:
        print(person.id, person.home, person.locationlog)
        #input()
print()
print('location log for each person, negative IDs indicate home')