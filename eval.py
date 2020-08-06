#!/usr/bin/env python3

import json
import rsa
from Crypto.Cipher import AES, PKCS1_OAEP

class Evaluate:

    def __init__(self, key_path):
        self.decryption_key = rsa.PrivateKey.load_pkcs1(open(key_path).read())
        # timeshift is added to every entry after initialized
        self.timeshift = 0

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
                



if __name__ == "__main__":
    ev = Evaluate("./private.pem")
    ev.read("data16.json")