#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
from time import time_ns

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.database = []
        self.log = []

    def handleDiscovery(self, dev, isNewDev, isNewData):
        self.log.append((time_ns(), dev))
        if isNewDev:
            self.database.append(dev.addr)
        # if isNewDev:
        #     print(f"New device {dev.addr}")
        # elif isNewData:
        #     print(f"New data from {dev.addr}: {dev}")



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