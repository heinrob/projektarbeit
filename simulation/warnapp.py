import random


### mainly for sending, receiving and storing rpis
class WarnApp:


    def __init__(self, smartphone):
        self.device = smartphone
        self.world = self.device.owner.world
        # randomly chosen timeslot to scan for other devices every 5 minutes
        self.scanTime = random.random() * self.world.constants['scanInterval']
        
        # save received rpis
        self.receivedRPIs = []

    def start(self):
        while True:
            # build rpi
            day = int(self.world.environment.now/3600/24)
            timeslot = int((self.world.environment.now - day * 3600 * 24) * self.world.constants['timeslots'] / 3600 / 24)
            rpi = f"0{self.device.id:011x}{day:012x}{timeslot:08x}"

            # initialize scan every 5 minutes at selected timeslot
            if int(self.world.environment.now - self.scanTime) % self.world.constants['scanInterval'] in range(self.world.constants['scanDuration']):

                self.world.environment.process(self.device.owner.location.scanRPI(self, self.device.owner.sublocation))

            self.device.owner.location.sendRPI(rpi, self.device.owner.sublocation)
            yield self.world.environment.timeout(random.random()*0.07+0.2) # see specification


    def receiveRPI(self, time, rssi, rpi):
        self.receivedRPIs.append((time, rssi, rpi))