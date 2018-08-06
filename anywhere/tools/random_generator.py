import os
from tools.encryptor import get_sha256_from_byte


def gen_random(digits=30):
    return os.urandom(digits)


def get_random_sha(digits=30):
    return get_sha256_from_byte(gen_random(digits))


