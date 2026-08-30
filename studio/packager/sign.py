import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

KEYS_DIR = os.path.join(os.path.dirname(__file__), "keys", "dev")

def get_or_create_keys():
    priv_path = os.path.join(KEYS_DIR, "dev_key.pem")
    pub_path = os.path.join(KEYS_DIR, "dev_key.pub.pem")

    if not os.path.exists(priv_path):
        os.makedirs(KEYS_DIR, exist_ok=True)
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        with open(priv_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(pub_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    with open(priv_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    return private_key

def sign_data(data: bytes) -> bytes:
    private_key = get_or_create_keys()
    return private_key.sign(data)
