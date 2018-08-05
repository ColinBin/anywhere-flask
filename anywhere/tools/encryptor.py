import hashlib


def get_sha256(raw_str):
    return hashlib.sha256(str.encode(raw_str)).hexdigest()


