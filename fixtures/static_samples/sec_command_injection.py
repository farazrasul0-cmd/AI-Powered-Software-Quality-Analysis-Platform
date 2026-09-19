# Vulnerable to Command Injection (CWE-78)
import subprocess

def ping_host(host_ip):
    # Flawed: subprocess with shell=True
    return subprocess.run(f"ping {host_ip}", shell=True, capture_output=True)
