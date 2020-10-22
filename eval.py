#!/usr/bin/env python3

import json
import rsa
from Crypto.Cipher import AES, PKCS1_OAEP

import argparse
import os

import datetime

def parsePacket(packet):
    pointer = 0
    parsed = []
    while pointer < len(packet):
        length = int(packet[pointer:pointer+2], base=16) * 2
        parsed.append(BLEPacket(packet[pointer:pointer+length+2]))
        pointer += length + 2
    return parsed


class BLEPacket:

    def __init__(self, packet):
        self.length = packet[:2]
        self.type = packet[2:4]
        self.payload = packet[4:]

    def __repr__(self):
        return f"{self.length} {self.type} {self.payload}"

class Evaluate:

    SLICE_DURATION = 10*60

    def __init__(self, key_path):
        self.decryption_key = rsa.PrivateKey.load_pkcs1(open(key_path).read())
        # timeshift is added to every entry after initialized
        self.timeshift = 0
        self.uniques = dict()
        self.sliceStart = 0
        self.slice = []
        self.locations = []

    def walk(self, foldername):
        for _, _, files in os.walk(foldername):
            for filename in sorted(files, key=lambda n: int(n[4:-5])): # TODO: only works if convertible
                f = os.path.join(foldername, filename)
                self.read(f)
                print(f)
        #counter = 0
        print(len(self.uniques))
                #input()

    def read(self, filename):
        with open(filename, "r") as encrypted:
            # first line is session key
            session_key = encrypted.readline()
            session_key = bytes.fromhex(session_key)
            session_key = rsa.decrypt(session_key, self.decryption_key)

            # second line is init vector
            iv = encrypted.readline()
            iv = bytes.fromhex(iv)
            iv = rsa.decrypt(iv, self.decryption_key)
            #print(session_key, iv)


            cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)
            for line in encrypted.readlines():
                line = line.replace("\n", "")
                event = cipher_aes.decrypt(bytes.fromhex(line))
                event = event.decode("utf-8")
                event = json.loads(event)
                self.handleEvent(event)

            # correct timing of all events

    def handleEvent(self,event):
        # set the correct time shift only for the first time
        if event['payload'].startswith("02011a1aff4c000215ffffffffffffffffffffffff") and self.timeshift == 0:
            time = event['payload'][42:50]
            time = int(time,base=16)
            self.timeshift = time - float(event['time'])
            print(self.timeshift)
        else:
            self.sliceEvents(event)

    def sliceEvents(self, event):
        if self.timeshift == 0:
            return
        time = float(event['time']) + self.timeshift
        if self.sliceStart + Evaluate.SLICE_DURATION <= time:
            self.sliceStart = time
            if len(self.slice) > 0:
                # do json magic here
                devices_count = len(set([e[0] for e in self.slice]))
                warn_app_devices = set([e[0] for e in self.slice if e[2].upper()[10:14] == "6FFD"])
                dt = datetime.datetime.fromtimestamp(time).strftime("%c")
                print(dt, devices_count, len(warn_app_devices))
                #print(warn_app_devices)
                typecounter = dict()
                typecounter["6FFD"] = 0
                rssimin = 0
                rssimax = -100
                for x in self.slice:
                    for packet in parsePacket(x[2]):
                        if packet.type not in typecounter:
                            typecounter[packet.type] = 1
                        else:
                            typecounter[packet.type] += 1
                    if x[2].upper()[10:14] == "6FFD":
                        #print(x)
                        rssimin = min(rssimin, x[1])
                        rssimax = max(rssimax, x[1])
                    #     typecounter["6FFD"] += 1
                    # print(x[2], parsePacket(x[2]))
                    #input()
                    # if x[0] in warn_app_devices and not x[2].upper()[10:14] == "6FFD":
                    #     print(x)
                    # if x[2][8:10] == "16":
                    #     print(x)
                    # if x[2][8:10] in ["08","09"]:
                    #     try:
                    #         print(bytearray.fromhex(x[2][10:]).decode())
                    #     except UnicodeDecodeError:
                    #         print(x[2][10:])
                    # else:
                    #     try:
                    #         print(f"{int(x[2][8:10], base=16):08b}")
                    #     except ValueError:
                    #         print(x)
                #input()
                #print(typecounter)
                print(rssimin, rssimax)
                input()
                self.slice = []
        self.slice.append([event['addr'], event['rssi'], event['payload']])

    def countUniqueRPIs(self, event):
        if event['payload'].upper()[10:14] == "6FFD":
            if event['payload'] in self.uniques:
                self.uniques[event['payload']] += 1
            else:
                self.uniques[event['payload']] = 1



if __name__ == "__main__":
    ev = Evaluate("./private.pem")

    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--location-size", '-l')
    args = parser.parse_args()
    ev.walk(args.folder)
