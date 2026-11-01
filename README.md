# HomePanel

A self-hosted, tablet-friendly home server dashboard with a macOS-inspired Liquid Glass interface.

## Features
- Live CPU, RAM, disk and optional NVIDIA GPU monitoring
- QR-based file upload from a phone or tablet
- Responsive web dashboard served by your Ubuntu server
- Runs as a dedicated, unprivileged Linux user

## Requirements
- Ubuntu Server 24.04 (other systemd-based Linux distributions may work)
- Python 3.10+
- Optional: NVIDIA drivers and `nvidia-smi` for GPU metrics

## Install
```bash
git clone https://github.com/kefy266/homepanel.git
cd homepanel
sudo bash install.sh
```

The installer creates `/opt/homepanel`, a dedicated `homepanel` service user, a Python virtual environment and a systemd service. It generates an admin password and prints it once. Save it securely.

Open `http://SERVER-IP:8787` from a device on your LAN or trusted VPN.

## Update
```bash
cd homepanel
sudo bash update.sh
```

## Security
- Keep port 8787 on your LAN or trusted VPN. Do not expose it directly to the public internet.
- The generated password is stored in `/etc/homepanel.env`, not in this repository.
- Uploaded files are stored in `/srv/homepanel/uploads`.
- Upload links expire after 10 minutes and are single-use.
- Never commit passwords, private keys, `.env` files or personal files.

## License
MIT. See [LICENSE](LICENSE).
