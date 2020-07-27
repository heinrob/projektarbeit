#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print(f"New device {dev.addr}")
        elif isNewData:
            print(f"New data from {dev.addr}: {dev}")



if __name__ == "__main__":

    while True:
        scanner = Scanner().withDelegate(DefaultDelegate())
        devices = scanner.scan(10.0)

        for dev in devices:
            print(f"Device {dev.addr} ({dev.addrType}), RSSI={dev.rssi} dB")
            for (adtype, desc, value) in dev.getScanData():
                print("  {desc} = {value}")