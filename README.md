# Reverse SSH Proxy Tunnel

Transform a **target machine** into a **SOCKS5 proxy** using a **reverse SSH tunnel**.

## SSH Flow Comparison

```text
======================= WELCOME TO REVERSE SSH =======================

=> Standard SSH Authentication flow (4 Steps):

SSH CLIENT (PUBKEY) ------------------> SSH HOST (AUTH PUBKEY)
SSH CLIENT (SOCKS5 TRY) <------------> SSH HOST (Crypto Challenge)

----------------------------------------------------------------------

=> Reverse SSH Authentication flow (2 Steps):

SSH HOST (AUTH KEYS) <---------------> SSH CLIENT (Authorized Tunnel SOCKS5)

**********************************************************************
                                                  CREATED BY: LUCAS LEBLANC
=======================================================================
```

## Environments Supported

* **Linux**
* **Termux** (Android)

- IP scraping in Termux relies on **CWE-200 vulnerability** (information disclosure without root). This may stop working in future versions.

### Confirmed Working:

* net-tools: v2.10 or lower
* termux: v2025.01.18 or lower
* android: v12 SKQ1.211019.001 or lower

---

## Configuration Script Overview (Host Setup)

### `install_packages()` / `install_tmx_pkgs()`

* Installs required packages:

  * `ssh`, `sshpass`, `scp`, `ufw`, `net-tools`
* Auto-detects if system is Termux and chooses proper package manager (`apt` or `pkg`).

### `sshd_setup()`

* Updates and configures `sshd_config`:

  * Port: `2222`
  * Enables GatewayPorts, TCP forwarding, key auth
  * Disables root login and password auth
  * Starts/restarts sshd

### `firewall_setup()` (Linux only)

* Configures `ufw`:

  * Allows port `2222` (SSH)
  * Blocks SOCKS5 port externally, allows only localhost

### `ssh_keygen()`

* Generates `id_ed25519` keypair
* Adds public key to `~/.ssh/authorized_keys`

### `sync_credentials()`

* Transfers SSH credentials to the client via `scp`
* Runs a remote command to ensure public key is added and authorized on the client

---

## Automation Features

| Feature            | Description                                                 |
| ------------------ | ----------------------------------------------------------- |
| `STEALTH_MODE`     | Suppresses all logs/output and disables sudo/root commands  |
| `SOCKS5_PORT`      | Configurable, default: `1080`                               |
| `AUTO HOST_USER`   | Automatically detected using `$USER` or `getpass.getuser()` |
| `AUTO SUPER_USER`  | Uses `sudo` unless in Termux or `STEALTH_MODE=True`         |
| `CLEAR_TEMP_FILES` | Temp files cleaned from `/tmp` or `~/.proxy_temp`           |

---

## How to Run (Host)

```bash
python3 ProxyConfig.py
```

Make sure:

* You can SSH into the client device with user/pass `tempass1234`
* The client is listening and reachable at `CLIENT_IP`

---

## Client Functions

These are the required client-side functions for establishing the reverse tunnel.

### `write_private_key(host_privkey)`

* Saves the host's private key to `~/.ssh/id_ed25519`

### `write_public_key(host_pubkey)`

* Saves the host's public key to `~/.ssh/id_ed25519.pub`

### `update_known_hosts(host_ip)`

* Ensures SSH fingerprint is accepted to avoid prompts

### `start_tunnel(host_user, host_ip)`

* Creates a SOCKS5 proxy tunnel to the host:

  ```bash
  ssh -i ~/.ssh/id_ed25519 -N -D 1080 -p 2222 {host_user}@{host_ip}
  ```

Use this SOCKS5 proxy at `127.0.0.1:1080` (or your custom port) in browsers or tools.

---

## File Structure (Auto-generated)

```text
/tmp/
├── host_privkey.txt
├── host_pubkey.txt
└── host_info.txt
```

---

## Test Setup (LAN)

```python
CLIENT_USER = "temp_user"
CLIENT_IP = "192.168.1.3"  # Example local IP
```

---

## Done

* SSH host and client configured
* SOCKS5 proxy tunnel active via reverse SSH
* Use `127.0.0.1:{SOCKS5_PORT}` as proxy

---

## License

MIT or specify your own

---
