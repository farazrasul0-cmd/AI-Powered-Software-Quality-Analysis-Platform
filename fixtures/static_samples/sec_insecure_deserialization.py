# Vulnerable to Insecure Deserialization (CWE-502)
import pickle

def restore_session(raw_bytes):
    # Flawed: unpickling untrusted input
    return pickle.loads(raw_bytes)
