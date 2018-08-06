import hashlib


def get_sha256(raw_str):
    return get_sha256_from_byte(str.encode(raw_str))


def get_sha256_from_byte(byte_seq):
    return hashlib.sha256(byte_seq).hexdigest()
