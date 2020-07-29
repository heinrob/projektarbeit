#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
import datetime

class ScanDelegate(DefaultDelegate):

    def __init__(self, fd):
        DefaultDelegate.__init__(self)
        self.database = []
        self.log = []
        self.fd = fd

    def handleDiscovery(self, dev, isNewDev, isNewData):
        time = datetime.datetime.now().timestamp()
        self.log.append((time, dev))
        self.fd.write(",".join([f"{time:.6f}", str(dev.addr), str(dev.rssi), *[f"{d}={v}" for (_,d,v) in dev.getScanData()]]))
        self.fd.write("\n")
        if isNewDev and not dev.addr in self.database:
            self.database.append(dev.addr)
            print(f"[ \033[31mNEW\033[39m ] - {dev.addr}")
        if isNewData:
            self.print(time, dev)
        #     print(f"New data from {dev.addr}: {dev}")

    def format_time(self, time):
        return datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S.%f")

    def print(self, time, dev):
        time = self.format_time(time)
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

    # group data for single device id
    def print_devices(self, cov_only=False):
        devices = dict()
        for entry in self.log:
            if entry[1].addr not in devices:
                devices[entry[1].addr] = [(entry[0], entry[1].getScanData()),]
            else:
                devices[entry[1].addr].append((entry[0], entry[1].getScanData()))
        
        for device in devices.keys():
            device_values = []
            print(f"[ \033[32m{device}\033[39m ]")
            for entry in devices[device]:
                out = f"    {self.format_time(entry[0])}\n"
                new_data = False
                for (_, desc, value) in entry[1]:
                    if not cov_only:
                        if value not in device_values:
                            out += f"        {desc} = {value}\n"
                            new_data = True
                            device_values.append(value)
                    else:
                        if desc == "16b Service Data" and value.startswith("6ffd"):
                            new_data = True
                        out += f"        {desc} = {value}\n"
                if new_data:
                    print(out)
            



if __name__ == "__main__":

    restarts = 0
    with open("restart_counter.txt", 'r') as f:
        restarts = int(f.readline())
    restarts += 1

    with open("restart_counter.txt", 'w') as f:
        f.write(f"{restarts}\n")

    with open(f"data{restarts}.csv", "a") as logfile:
        delegate = ScanDelegate(logfile)
        scanner = Scanner().withDelegate(delegate)

        try:
            while True:
                devices = scanner.scan(10.0)
        except KeyboardInterrupt:
            delegate.print_devices(True)
            print("[ QUIT ]")

        #delegate.print_log()
        # for dev in devices:
        #     print(f"Device {dev.addr} ({dev.addrType}), RSSI={dev.rssi} dB")
        #     for (adtype, desc, value) in dev.getScanData():
        #         print(f"  {desc} = {value}")
