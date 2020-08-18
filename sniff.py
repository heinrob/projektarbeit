#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate
import datetime
import json
import logging
import signal
import sys
from os.path import exists
import time
from subprocess import Popen

import rsa
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP

from os.path import isfile


def led_set(value):
    path = "/sys/class/leds/led0/brightness"
    if exists(path):
        with open(path, 'w') as ledfile:
            ledfile.write(f"{value}\n")

def led_interval(duration=1):
    led_set(1)
    time.sleep(duration)
    led_set(0)

class ScanDelegate(DefaultDelegate):

    def __init__(self, fd, cipher):
        DefaultDelegate.__init__(self)
        self.fd = fd
        self.cipher = cipher
        self.led_status = 0
        self.confirm_sync_acc = False

    def handleDiscovery(self, dev, isNewDev, isNewData):
        timestamp = datetime.datetime.now().timestamp()
        try:
            line = {"time": f"{timestamp:.6f}", "addr": dev.addr, "rssi": dev.rssi, "payload": dev.rawData.hex()}
        except AttributeError as e:
            if type(dev.rawData) is str:
                line = {"time": f"{timestamp:.6f}", "addr": dev.addr, "rssi": dev.rssi, "payload": dev.rawData}
            else:
                logging.error(e)
                line = ''
        self.write(json.dumps(line))
        self.led_status = 1 - self.led_status
        led_set(self.led_status)
        if line['payload'].startswith("02011a1aff4c000215ffffffffffffffffffffffff") and not self.confirm_sync_acc:
            logging.info("Sync packet received.")
            self.confirm_sync_acc = True
            Popen(["/home/pi/projektarbeit/led_code.sh"])

    def write(self, line):
        line += " "*(16-(len(line)%16)) # padding to 16 byte blocks, spaces should be irrelevant to json loads
        self.fd.write(f"{self.cipher.encrypt(line).hex()}\n")

    def format_time(self, time):
        return datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S.%f")

class Sniffer:

    def __init__(self):
        self.file_rotation = False

    def init_encryption(self):
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
        [ self.file_descriptor.write(x) for x in (enc_session_key.hex(), "\n", enc_iv.hex(), "\n") ]

        logging.info("Encryption initialization successful")
        return cipher_aes
        

    def create_file(self):
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

    def mainloop(self):
        filename = self.create_file()
        logging.info(f"Writing to file: {filename}")

        with open(filename, "a", buffering=1) as save_file:

            # initialize encryption
            self.file_descriptor = save_file
            cipher_aes = self.init_encryption()

            delegate = ScanDelegate(save_file, cipher_aes)
            scanner = Scanner().withDelegate(delegate)

            logging.debug("Scanning...")
            led_set(0)

            try:
                while not self.file_rotation:
                    scanner.scan(10.0)
                self.file_rotation = False
            except KeyboardInterrupt:
                logging.debug("[ QUIT ] - by KeyboardInterrupt")

if __name__ == "__main__":

    sniffer = Sniffer()

    def sigterm_handler(_signo, _stack_frame):
        # Raises SystemExit(0):
        try:
            logging.critical(f"SIGTERM triggered {_stack_frame}")
        except:
            pass
        sys.exit(0)

    def sigusr1_handler(_signum, _frame): # rotate files
        try:
            logging.info(f"SIGUSR1 triggered: rotating files")
            sniffer.file_rotation = True
        except:
            logging.critical("SIGUSR1 handling did not work")

    
    led_set(1)
    # setup signal handling and logging
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGUSR1, sigusr1_handler)
    logging.basicConfig(format="%(asctime)s>%(levelname)s:%(message)s",level=logging.DEBUG,filename='sniff.log')

    while True:
        sniffer.mainloop()
