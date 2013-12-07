from Crypto import Random
from Crypto.Cipher import AES
import base64

KEY = b'Sixteen byte key'
BLOCK_SIZE = 16 
class AESCipher:
    def __init__(self):
        self.key = KEY 
                 
    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) ) 

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return self.unpad(cipher.decrypt( enc[16:] ))

    def pad(self, s): 
    	return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE) 

    def unpad(self, s): 
    	return s[0:-ord(s[-1])]

    def new_key(self):
        return Random.new().read(32)

    def set_key(self, key):
    	self.key = key