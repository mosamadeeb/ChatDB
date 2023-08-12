import base64
from copy import copy
from hashlib import md5

from cryptography.fernet import Fernet

from common import DatabaseProps


def generate_key(password: str) -> bytes:
    # Generate an MD5 from the password and encode it to base64 to use as the Fernet encryption key
    return base64.urlsafe_b64encode(md5(password.encode("utf-8")).hexdigest().encode("latin-1"))


DEFAULT_KEY = generate_key("chat-db")


def encrypt(data: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data)


def decrypt(data: bytes, key: bytes) -> bytes:
    f = Fernet(key)
    return f.decrypt(data)


def encrypt_prop(v, encryption_key):
    def encrypt_attr(a):
        return encrypt(a.encode("utf-8"), encryption_key).decode("utf-8")

    # Create a copy to avoid updating the original value
    v = copy(v)

    if type(v).__name__ == DatabaseProps.__name__:
        v.uri = encrypt_attr(v.uri)

    return v


def decrypt_prop(v, encryption_key):
    def decrypt_attr(a):
        return decrypt(a.encode("utf-8"), encryption_key).decode("utf-8")

    if type(v).__name__ == DatabaseProps.__name__:
        v.uri = decrypt_attr(v.uri)

    return v
