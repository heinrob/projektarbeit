#!/usr/bin/env python3

#from Crypto.PublicKey import RSA
import rsa
from Crypto.Cipher import AES, PKCS1_OAEP

class Evaluate:

    def __init__(self, key_path):
        self.decryption_key = rsa.PrivateKey.load_pkcs1(open(key_path).read())

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
            print(session_key, iv)
            

            cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)
            for line in encrypted.readlines():
                line = line.replace("\n", "")
                data = cipher_aes.decrypt(bytes.fromhex(line))
                print(data.decode("utf-8"))



if __name__ == "__main__":
    ev = Evaluate("./private.pem")
    ev.read("data2.json")