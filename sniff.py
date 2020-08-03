#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
import datetime
import json

import rsa
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP

from os.path import isfile


class ScanDelegate(DefaultDelegate):

    def __init__(self, fd, cipher):
        DefaultDelegate.__init__(self)
        self.database = []
        self.log = []
        self.fd = fd
        self.cipher = cipher

    def handleDiscovery(self, dev, isNewDev, isNewData):
        time = datetime.datetime.now().timestamp()
        self.log.append((time, dev))
        try:
            line = {"time": f"{time:.6f}", "addr": dev.addr, "rssi": dev.rssi, "payload": dev.rawData.hex()}
        except AttributeError as e:
            if type(dev.rawData) is str:
                line = {"time": f"{time:.6f}", "addr": dev.addr, "rssi": dev.rssi, "payload": dev.rawData}
            else:
                print(e)
        self.write(json.dumps(line))

    def write(self, line):
        line += " "*(16-(len(line)%16)) # padding to 16 byte blocks, spaces should be irrelevant to json loads
        self.fd.write(f"{self.cipher.encrypt(line).hex()}\n") #hex?

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
            

def init_encryption(file_descriptor):
    encryption_key = rsa.PublicKey.load_pkcs1(open("public.pem").read())

    # Encrypt the session key with the public RSA key
    session_key = get_random_bytes(16)
    enc_session_key = rsa.encrypt(session_key, encryption_key)

    #generate iv for CBC
    iv = get_random_bytes(16)
    enc_iv = rsa.encrypt(iv, encryption_key)

    # Encrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)
    # first two lines of file contain session key and init vector
    [ file_descriptor.write(x) for x in (enc_session_key.hex(), "\n", enc_iv.hex(), "\n") ]

    print("Encryption initialization successful")
    return cipher_aes
    

def create_file():
    restarts = 0
    try:
        with open("restart_counter.txt", 'r') as f:
            restarts = int(f.readline())
    except FileNotFoundError:
        pass

    #skip existing files
    while True:
        restarts += 1
        filename = f"data{restarts}.json"
        if not isfile(filename):
            break

    with open("restart_counter.txt", 'w') as f:
        f.write(f"{restarts}\n")

    return filename

if __name__ == "__main__":

    filename = create_file()
    print(f"Writing to file: {filename}")

    with open(filename, "a") as save_file:

        # initialize encryption
        cipher_aes = init_encryption(save_file)

        delegate = ScanDelegate(save_file, cipher_aes)
        scanner = Scanner().withDelegate(delegate)

        print("Scanning...")

        try:
            while True:
                devices = scanner.scan(10.0)
        except KeyboardInterrupt:
            #delegate.print_devices(True)
            print("[ QUIT ]")
