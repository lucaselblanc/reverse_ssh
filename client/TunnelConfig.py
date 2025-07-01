#!/usr/bin/env python3
import os
import subprocess

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

HOST_INFO_FILE = os.path.expanduser("~/host_info.txt")
HOST_PRIVK_FILE = os.path.expanduser("~/host_privkey.txt")
HOST_PUBKEY_FILE = os.path.expanduser("~/host_pubkey.txt")

SOCKS5_PORT = "1080"
SSH_KEY_PATH = os.path.expanduser("~/.ssh/id_ed25519")

CLEAR_TEMP_FILES = False

def run(cmd, desc):
    print(f"{desc}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"{GREEN}OK{RESET}\n")
    except subprocess.CalledProcessError:
        print(f"{RED}Erro:{RESET} {CYAN}{desc}{RESET}")
        exit(1)

def read_files():
    if not (os.path.exists(HOST_INFO_FILE) and os.path.exists(HOST_PUBKEY_FILE) and os.path.exists(HOST_PRIVK_FILE)):
        print(f"{RED}Files with host information not found!{RESET}")
        exit(1)

    with open(HOST_INFO_FILE) as f:
        host_line = f.read().strip()

    with open(HOST_PRIVK_FILE) as f:
        host_privkey = f.read()

    with open(HOST_PUBKEY_FILE) as f:
        host_pubkey = f.read().strip()

    if "@" not in host_line:
        print(f"{RED}Invalid format in host_info.txt{RESET}")
        exit(1)

    host_user, host_ip = [x.strip() for x in host_line.split("@")]
    return host_user, host_ip, host_privkey, host_pubkey

def write_private_key(privkey_content):
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)

    with open(SSH_KEY_PATH, "w") as f:
        f.write(privkey_content)
    os.chmod(SSH_KEY_PATH, 0o600)
    print(f"{GREEN}Private key saved in{RESET} {CYAN}{SSH_KEY_PATH}{RESET}\n")

def write_public_key(pubkey_content):
    with open(SSH_KEY_PATH + ".pub", "w") as f:
        f.write(pubkey_content + "\n")
    print(f"{GREEN}Public key saved in{RESET} {CYAN}{SSH_KEY_PATH}.pub{RESET}\n")

def update_known_hosts(host_ip):
    known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
    os.makedirs(os.path.dirname(known_hosts_path), exist_ok=True)

    subprocess.run(["ssh-keygen", "-f", known_hosts_path, "-R", f"[{host_ip}]:2222"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        subprocess.run([
            "ssh",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-p", "2222",
            f"{host_ip}",
            "exit"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def start_tunnel(host_user, host_ip):
    print(f"{CYAN}Testing SSH connection with SOCKS5 tunnel{RESET}[{GREEN}...{RESET}]")
    try:
        subprocess.run([
            "ssh",
            "-i", SSH_KEY_PATH,
            "-D", SOCKS5_PORT,
            "-p", "2222",
            "-N",
            f"{host_user}@{host_ip}"
        ], check=True)
    except subprocess.CalledProcessError:
        print(f"{RED}Error connecting with SOCKS5 tunnel!{RESET}")
        exit(1)

def clean_temp_files():
    for path in [HOST_INFO_FILE, HOST_PRIVK_FILE, HOST_PUBKEY_FILE]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

def main():
    host_user, host_ip, host_privkey, host_pubkey = read_files()
    write_private_key(host_privkey)
    write_public_key(host_pubkey)
    update_known_hosts(host_ip)

    print(f"{YELLOW}Now you can start the SOCKS5 tunnel with:{RESET}")
    print(f"{GREEN}ssh{RESET} {RED}-i{RESET} {CYAN}{SSH_KEY_PATH}{RESET} {RED}-D{RESET} {GREEN}{SOCKS5_PORT}{RESET} {RED}-p{RESET} {GREEN}2222{RESET} {RED}-N{RESET} {CYAN}{host_user}{RESET}{RED}@{RESET}{CYAN}{host_ip}{RESET}\n")

    start_tunnel(host_user, host_ip)

    if CLEAR_TEMP_FILES:
        clean_temp_files()

if __name__ == "__main__":
    main()