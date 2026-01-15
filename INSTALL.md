# Oonanji Vault Installation Guide (for Ubuntu)

This guide explains the steps to install Oonanji Vault on a new Ubuntu PC from the GitHub repository and set up automatic startup.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation Steps](#2-installation-steps)
   - Install with Docker (Recommended)
   - Manual Installation
3. [Model File Placement](#3-model-file-placement)
4. [Auto-start Setup](#4-auto-start-setup)

---

## 1. Prerequisites

- **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- **Required Specs**:
  - Memory: 16GB or more recommended (Minimum 8GB)
  - Storage: 20GB or more free space
- **Internet Connection**: Required for initial setup

---

## 2. Installation Steps

### Method A: Install with Docker (Recommended)

This is the easiest and most stable method.

#### 1. Install Docker
Skip this if already installed.

```bash
# Run Docker official installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to Docker group (to use docker command without sudo)
sudo usermod -aG docker $USER

# Log out and log back in, or run the following to apply changes
newgrp docker
```

#### 2. Clone Repository
Get the source code from GitHub.

```bash
git clone https://github.com/your-org/oonanji-vault.git
cd oonanji-vault
```

#### 3. Start Containers

```bash
docker compose up -d
```

The system will start.
Access `http://localhost` in your browser to verify.

---

### Method B: Manual Installation

Steps to install directly without Docker.

#### 1. Install Required Tools

```bash
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip nodejs npm git
```

#### 2. Clone Repository

```bash
git clone https://github.com/your-org/oonanji-vault.git
cd oonanji-vault/system
```

#### 3. Backend Setup

```bash
# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Frontend Setup

```bash
# Return to project root if needed
npm install
npm run build
```

---

## 3. Model File Placement

⚠️ **Important**: AI models (`.gguf` files) are large and are NOT included in GitHub. You must prepare and place them separately.

You can download them from the Admin Dashboard or place them manually.

### Location
`oonanji-vault/system/models/`

### Example File Structure
```
system/models/
├── qwen2.5-coder-7b-instruct-q4_k_m.gguf  (For Chat)
└── nomic-embed-text-v1.5.f16.gguf         (For Search/Embedding)
```

The system will automatically recognize model files placed in this folder.

---

## 4. Auto-start Setup

Configure Oonanji Vault to start automatically when the PC powers on.

### Pattern A: Using Docker (Easiest)

Set the restart policy for containers started with Docker Compose.

```bash
# Configure containers to restart automatically unless explicitly stopped
docker update --restart unless-stopped oonanji-vault-backend-1
docker update --restart unless-stopped oonanji-vault-frontend-1
```

* You can check container names with `docker ps`.

### Pattern B: Using Systemd (For Manual Install)

Create and manage a `systemd` service file.

1. Create a service file:
```bash
sudo nano /etc/systemd/system/oonanji-vault.service
```

2. Paste the following content and save (`Ctrl+O`, `Enter`, `Ctrl+X`):
   * Change `User=ubuntu` to your username.
   * Change `/path/to/oonanji-vault` to your actual path.

```ini
[Unit]
Description=Oonanji Vault Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/oonanji-vault
# Path to startup script
ExecStart=/home/ubuntu/oonanji-vault/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and Start the Service:

```bash
# Reload daemon
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable oonanji-vault.service

# Start now
sudo systemctl start oonanji-vault.service
```

### How to Check Status

```bash
sudo systemctl status oonanji-vault.service
```

Success if you see a green light (active (running)).
