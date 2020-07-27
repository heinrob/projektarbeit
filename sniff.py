#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
import datetime

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.database = []
        self.log = []

    def handleDiscovery(self, dev, isNewDev, isNewData):
        time = datetime.datetime.now().timestamp()
        self.log.append((time, dev))
        if isNewDev and not dev.addr in self.database:
            self.database.append(dev.addr)
            print(f"[ \033[31mNEW\033[39m ] - {dev.addr}")
        if isNewData:
            self.print(time, dev)
        #     print(f"New data from {dev.addr}: {dev}")

    def print(self, time, dev):
        time = datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"[ \033[32m{time}\033[39m ] - {dev.addr} ({dev.rssi})")
        for (_, desc, value) in dev.getScanData():
            print(f"  {desc} = {value}")

    def print_log(self):
        existing = []
        for entry in self.log:
            if entry[1].addr not in existing:
                existing.append(entry[1].addr)
                print(f"[ NEW ] - {entry[1].addr}")
            self.print(*entry)
            



if __name__ == "__main__":

    delegate = ScanDelegate()
    scanner = Scanner().withDelegate(delegate)

    try:
        while True:
            devices = scanner.scan(10.0)
    except KeyboardInterrupt:
        print("[ QUIT ]")

        #delegate.print_log()
        # for dev in devices:
        #     print(f"Device {dev.addr} ({dev.addrType}), RSSI={dev.rssi} dB")
        #     for (adtype, desc, value) in dev.getScanData():
        #         print(f"  {desc} = {value}")
