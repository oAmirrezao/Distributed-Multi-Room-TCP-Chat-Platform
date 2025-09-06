import bcrypt
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class SecurityManager:
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    @staticmethod
    def verify_password(password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    @staticmethod
    def generate_key():
        return os.urandom(32)  # 256-bit key
    
    @staticmethod
    def encrypt_data(data, key):
        iv = os.urandom(16)  # 128-bit IV
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return iv + encrypted
    
    @staticmethod
    def decrypt_data(encrypted_data, key):
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        padded = decryptor.update(encrypted) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded) + unpadder.finalize()
        return data
