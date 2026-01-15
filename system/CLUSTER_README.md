# Oonanji AI Cluster Guide

This system supports distributed inference across multiple computers with NVIDIA GPUs (using CUDA) or CPU fallback.

## 1. Main Computer Setup
The main computer runs the User Interface and coordinates the AI.

1. **Install & Run**:
   Ensure your `.env` or environment has `CLUSTER_NODES` set if you have workers. If running alone, leave it empty.
   ```bash
   docker compose up --build -d
   ```

2. **Configuration**:
   To add worker nodes later, edit `docker-compose.yml` or export the variable:
   ```yaml
   environment:
     - CLUSTER_NODES=http://192.168.1.11:8000,http://192.168.1.12:8000
   ```

## 2. Worker (Sub) Computer Setup
For every other computer you want to add to the cluster:

1. **Install Ubuntu**: Access the terminal.
2. **Copy the Setup Script**:
   Copy the `cluster_components/setup_worker.sh` file from this project to the worker computer (e.g., via USB or SSH).
3. **Run the Script**:
   ```bash
   chmod +x setup_worker.sh
   ./setup_worker.sh
   ```
   This script will:
   - Install Docker & NVIDIA Drivers (if GPU found).
   - Start the AIWorker.
4. **Register**:
   Get the expansion IP (e.g., `192.168.1.XX`) and add it to the Main Computer's `CLUSTER_NODES` list.

## 3. Architecture
- **Main Node**: Handles Web UI, RAG (Documents), and Load Balancing.
- **Worker Nodes**: Pure inference engines. They receive a prompt and return the text.
- **Failover**: If a worker fails, the system currently does not auto-retry (future enhancement), but you can simply remove it from the list.

## 4. Troubleshooting
- **GPU not used?** Check `nvidia-smi` on the worker. Ensure the configured model matches what is in the worker's `/models` folder.
- **Connection Error?** Ensure all PCs are on the same network (Use a switch/hub) and have static IPs. Check firewall (`sudo ufw allow 8000`).
