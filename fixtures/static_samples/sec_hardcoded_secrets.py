# Vulnerable to Hardcoded Credentials (CWE-798)
def authenticate_service():
    api_key = "ak_live_99214a8b7c6d5e4f3a2b1c0d"
    password = "SuperSecretMasterKey2026!"
    return api_key, password
