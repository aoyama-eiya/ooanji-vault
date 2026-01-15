#!/bin/bash
set -e

echo "【NVIDIA Container Toolkit のセットアップを開始します】"
echo "管理者権限(sudo)が必要です。パスワードを求められたら入力してください。"
echo ""

# リポジトリの追加
echo "1. NVIDIAリポジトリを追加中..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  || { echo "GPGキーの追加に失敗しました"; exit 1; }

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
  || { echo "リポジトリリストの作成に失敗しました"; exit 1; }

# インストール
echo "2. APTを更新してインストール中..."
sudo apt-get update || echo "警告: 一部のリポジトリの更新に失敗しましたが、インストールを続行します..."
sudo apt-get install -y nvidia-container-toolkit

# 設定
echo "3. Dockerランタイムを設定中..."
sudo nvidia-ctk runtime configure --runtime=docker

# 再起動
echo "4. Dockerを再起動中..."
sudo systemctl restart docker

echo ""
echo "=========================================="
echo "  セットアップが完了しました！"
echo "  再度 'docker compose up --build -d' を実行してください。"
echo "=========================================="
