#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
import datetime

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.database = []
        self.log = []

    def handleDiscovery(self, dev, isNewDev, isNewData):
        self.log.append((datetime.datetime.timestamp(), dev))
        if isNewDev:
            self.database.append(dev.addr)
        # if isNewDev:
        #     print(f"New device {dev.addr}")
        # elif isNewData:
        #     print(f"New data from {dev.addr}: {dev}")

    def print(self, time, dev):
        time = datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"[ {time} ] - {dev.addr} ({dev.rssi})")
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

    while True:
        devices = scanner.scan(10.0)

        print(delegate.log)
        # for dev in devices:
        #     print(f"Device {dev.addr} ({dev.addrType}), RSSI={dev.rssi} dB")
        #     for (adtype, desc, value) in dev.getScanData():
        #         print(f"  {desc} = {value}")