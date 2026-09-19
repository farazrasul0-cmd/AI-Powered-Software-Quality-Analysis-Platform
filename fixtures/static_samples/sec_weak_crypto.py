# Vulnerable to Weak Cryptographic Hash (CWE-327)
import hashlib

def compute_checksum(data):
    # Flawed: MD5 is cryptographically broken
    return hashlib.md5(data.encode()).hexdigest()
