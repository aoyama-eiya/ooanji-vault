#!/bin/bash
set -e

# Oonanji AI Cluster - Worker Setup Script
# Run this on your SUB (Worker) PCs (Ubuntu).

echo "=== Oonanji AI Cluster Worker Setup ==="

# 1. Check for NVIDIA GPU
HAS_GPU=false
if lspci | grep -i nvidia > /dev/null; then
    echo "[✅] NVIDIA GPU detected."
    HAS_GPU=true
else
    echo "[ℹ️] No NVIDIA GPU detected. Will run in CPU-only mode."
fi

# 2. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[*] Installing Docker..."
    # Standard Docker installation for Ubuntu
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "[✅] Docker is already installed."
fi

# 3. Install NVIDIA Container Toolkit if GPU is present
if [ "$HAS_GPU" = true ]; then
    if ! dpkg -l | grep nvidia-container-toolkit > /dev/null; then
        echo "[*] Installing NVIDIA Container Toolkit..."
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
            && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        
        sudo apt-get update
        sudo apt-get install -y nvidia-container-toolkit
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo systemctl restart docker
        echo "[✅] NVIDIA Toolkit installed."
    else
        echo "[✅] NVIDIA Toolkit already installed."
    fi
fi

# 4. Create Worker Configuration
WORKER_DIR="$HOME/oonanji-worker"
mkdir -p "$WORKER_DIR"
cat <<EOF > "$WORKER_DIR/docker-compose.yml"
version: '3.8'

services:
  inference-worker:
    image: ghcr.io/abetlen/llama-cpp-python:latest
    ports:
      - "8000:8000"
    environment:
      - USE_MLOCK=1     # Lock memory to prevent swapping
      - N_GPU_LAYERS=-1 # Offload all layers to GPU
    volumes:
      - ./models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    command: python3 -m llama_cpp.server --model /models/default_model.gguf --host 0.0.0.0 --port 8000 --n_gpu_layers -1 --verbose True
EOF

# CPU Fallback adjustment
if [ "$HAS_GPU" = false ]; then
    # Remove nvidia reservation for CPU only
    sed -i '/deploy:/,+5d' "$WORKER_DIR/docker-compose.yml"
fi

echo "=== Setup Complete ==="
echo "To start the worker:"
echo "1. Place your .gguf model file in $WORKER_DIR/models/ and rename it to 'default_model.gguf'"
echo "2. Run: cd $WORKER_DIR && sudo docker compose up -d"
echo ""
echo "=== IMPORTANT: Registering to Main PC ==="
echo "Get this computer's IP address (run 'hostname -I')."
echo "Add it to the Main PC's configuration environment variable:"
echo "CLUSTER_NODES=http://<THIS_IP>:8000"
