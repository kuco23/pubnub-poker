from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

keydir = Path('keys')
keydir.mkdir(exist_ok=True)
prvkfp = keydir / 'private_key.pem'
pubkfp = keydir / 'public_key.pem'

def _keygen():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())
    public_key = private_key.public_key()
    
    spriv = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption())
    spub = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    
    with open(prvkfp, 'wb') as f: f.write(spriv)
    with open(pubkfp, 'wb') as f: f.write(spub)
    
    return private_key, public_key

def _prvkeyread():
    with open(prvkfp, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), None, default_backend())
    return private_key

def _pubkeyread():
    with open(pubkfp, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(), default_backend())
    return public_key
    
def prvkeyget():
    if prvkfp.exists():
        return _prvkeyread() 
    prv, _ = _keygen()
    return prv

def pubkeyget():
    if pubkfp.exists(): 
        return _pubkeyread()
    _, pub = _keygen()
    return pub

def pubkeyserialized(pub):
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

def pubkeydeserialized(ser):
    return serialization.load_pem_public_key(
        ser.encode(), backend=default_backend())

def encrypt(pbk, data):
    return pbk.encrypt(data.encode(), padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )).hex()

def decrypt(prk, encr):
    return prk.decrypt(bytes.fromhex(encr), padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )).decode()
        