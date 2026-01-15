# Oonanji Vault - 本番環境セットアップガイド

## 🚀 クイックスタート

### 1. 初回セットアップ

```bash
# 1. 依存関係のインストール
npm install

# 2. Python仮想環境のセットアップ
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. モデルファイルの配置
# models/ディレクトリに以下を配置:
# - チャット用GGUFモデル (例: qwen2.5-coder-7b-instruct-q4_k_m.gguf)
# - 埋め込み用モデル (nomic-embed-text-v1.5.f16.gguf)
```

### 2. サーバーの起動

```bash
# 一つのコマンドで両方のサーバーを起動
./start.sh
```

これで以下が起動します:
- **フロントエンド**: http://localhost (ポート80)
- **バックエンドAPI**: http://localhost:8000

### 3. サーバーの停止

```bash
./stop.sh
```

## 📋 デフォルトアカウント

- **ユーザー名**: `adminuser`
- **パスワード**: `admin`

## 🔧 本番環境の設定

### ポート80の使用について

ポート80を使用するため、`start.sh`はsudo権限を要求します。
初回起動時にパスワードを入力してください。

### 自動起動の設定（オプション）

システム起動時に自動的にサーバーを起動したい場合:

```bash
# systemdサービスファイルを作成
sudo nano /etc/systemd/system/oonanji.service
```

以下の内容を記述:

```ini
[Unit]
Description=Oonanji Vault Service
After=network.target

[Service]
Type=forking
User=eiya
WorkingDirectory=/out
ExecStart=/out/start.sh
ExecStop=/out/stop.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービスを有効化:

```bash
sudo systemctl daemon-reload
sudo systemctl enable oonanji
sudo systemctl start oonanji
```

## 🌐 ネットワークアクセス

### 同じネットワーク内の他の端末からアクセス

1. サーバーのIPアドレスを確認:
```bash
ip addr show
```

2. 他の端末から以下のURLでアクセス:
```
http://<サーバーのIPアドレス>
```

例: `http://192.168.1.100`

### ファイアウォールの設定

ポート80と8000を開放する必要がある場合:

```bash
# UFWの場合
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp

# firewalldの場合
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 📁 NASの設定

### NASのマウント

```bash
# 手動マウント
sudo mount -t cifs //192.168.1.100/share ./mnt -o username=admin,password=yourpass

# 永続的なマウント（/etc/fstabに追加）
echo "//192.168.1.100/share /out/mnt cifs username=admin,password=yourpass,uid=1000,gid=1000 0 0" | sudo tee -a /etc/fstab
```

### 内部ストレージの使用

NASがない場合は、`internal_storage/`ディレクトリを使用できます。
管理画面からストレージモードを切り替えてください。

## 🔍 ログの確認

```bash
# バックエンドのログ
tail -f logs/backend.log

# フロントエンドのログ
tail -f logs/frontend.log

# リアルタイムで両方を表示
tail -f logs/*.log
```

## 🛠️ トラブルシューティング

### ポート80が使用中

```bash
# ポート80を使用しているプロセスを確認
sudo lsof -i :80

# 必要に応じて停止
sudo systemctl stop apache2  # Apacheの場合
sudo systemctl stop nginx    # Nginxの場合
```

### サーバーが起動しない

```bash
# ログを確認
cat logs/backend.log
cat logs/frontend.log

# 手動で起動してエラーを確認
source venv/bin/activate
python backend.py

# 別のターミナルで
npm run dev
```

### データベースのリセット

```bash
# ユーザーデータベースを削除（注意: すべてのユーザーが削除されます）
rm users.db

# 次回起動時にデフォルト管理者が再作成されます
./start.sh
```

### インデックスのリセット

```bash
# ChromaDBを削除
rm -rf chroma_db/

# 管理画面から再度インデックス化を実行してください
```

## 📊 システム要件

### 最小要件
- **CPU**: 4コア以上
- **RAM**: 8GB以上
- **ストレージ**: 20GB以上の空き容量

### 推奨要件
- **CPU**: 8コア以上
- **RAM**: 16GB以上（大きなモデルの場合32GB）
- **GPU**: NVIDIA GPU（CUDA対応）またはIntel GPU（OpenCL対応）
- **ストレージ**: SSD 50GB以上

## 🔐 セキュリティ

### パスワードの変更

初回ログイン後、必ず管理者パスワードを変更してください:
1. 管理画面にログイン
2. ユーザー管理で新しい管理者を作成
3. デフォルトの`adminuser`を削除

### HTTPS化（オプション）

本番環境でHTTPSを使用する場合は、Nginxをリバースプロキシとして設定することを推奨します。

## 📝 メンテナンス

### バックアップ

重要なデータをバックアップ:

```bash
# データベース
cp users.db users.db.backup

# ChromaDB
tar -czf chroma_db_backup.tar.gz chroma_db/

# 設定ファイル
cp .env.example .env.backup
```

### アップデート

```bash
# Gitリポジトリの場合
git pull

# 依存関係の更新
source venv/bin/activate
pip install -r requirements.txt --upgrade
npm install

# サーバーの再起動
./stop.sh
./start.sh
```

## 📞 サポート

問題が発生した場合:
1. ログファイルを確認
2. README.mdのトラブルシューティングセクションを参照
3. GitHubのIssuesで報告

## 🎯 次のステップ

1. ✅ サーバーを起動
2. ✅ http://localhost でアクセス
3. ✅ デフォルトアカウントでログイン
4. ✅ 管理画面で新しいユーザーを作成
5. ✅ NASをマウント（または内部ストレージを使用）
6. ✅ インデックス化を実行
7. ✅ チャットでDB検索を試す

お疲れ様でした! 🎉
