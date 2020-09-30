#!/usr/bin/env python3

import json
import rsa
from Crypto.Cipher import AES, PKCS1_OAEP

import argparse
import os

class Evaluate:

    def __init__(self, key_path):
        self.decryption_key = rsa.PrivateKey.load_pkcs1(open(key_path).read())
        # timeshift is added to every entry after initialized
        self.timeshift = 0
        self.uniques = dict()

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
            if event['payload'].upper()[10:14] == "6FFD":
                if event['payload'] in self.uniques:
                    self.uniques[event['payload']] += 1
                else:
                    self.uniques[event['payload']] = 1
                



if __name__ == "__main__":
    ev = Evaluate("./private.pem")

    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()
    ev.walk(args.folder)