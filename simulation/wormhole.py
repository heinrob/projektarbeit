import random


### send rpis from $locations to $destinations
class Wormhole:
    
    def __init__(self, wormhole_js, world):
        self.world = world
        self.id = wormhole_js['id']
        self.receiveFrom = wormhole_js['receive']
        self.sendTo = wormhole_js['send']
        for entry in range(len(self.sendTo)):
            if self.sendTo[entry][1] == -1:
                self.sendTo[entry][1] = random.randrange(0, len(self.world.locations[self.sendTo[entry][0]].sublocations))

    # send received rpi to all connected wormhole senders
    def sendRPI(self, rpi):
        wormholebit = int(rpi[0], base=16)
        if wormholebit < 0xf:
            wormholebit += 1
        updatedRPI = f"{wormholebit:1x}{rpi[1:]}"
        for lidx, sublocation in self.sendTo:
            self.world.locations[lidx].sendRPI(updatedRPI, sublocation)
