# Oonanji Vault - クイックスタートガイド

## 🎯 概要

このプロジェクトは完全にセットアップされ、すぐに使用できる状態です！

## ✅ 完了した作業

### 1. Python環境
- ✅ Python 3.9仮想環境（venv）作成済み
- ✅ `mnt`フォルダ作成済み（NASマウント用）
- ✅ バックエンドスクリプト（backend.py）実装済み

### 2. Next.jsアプリケーション
- ✅ Next.js + TypeScript + Tailwind CSS
- ✅ ログイン画面（管理者/ユーザー切り替え対応）
- ✅ ダッシュボード（チャットインターフェース）
- ✅ 管理者画面（ユーザー管理、AIモデル管理、NAS設定、ネットワーク設定）
- ✅ 設定モーダル（テーマ、フォントサイズ、言語、通知、パーソナライズ）

### 3. 機能
- ✅ AIモデル切り替え（GGUF形式対応）
- ✅ GPU対応（NVIDIA CUDA、Intel統合GPU）
- ✅ NAS接続設定
- ✅ ユーザー管理
- ✅ ダークモード/ライトモード
- ✅ レスポンシブデザイン

## 🚀 使用方法

### 開発サーバーの起動

現在、開発サーバーは既に起動しています：
```
http://localhost:3000
```

### ログイン

**テストモード（開発用）**:

1. **管理者としてログイン**:
   - クイックログインボタン「管理者」をクリック
   - または、ユーザー名: `admin`、パスワード: `admin`

2. **ユーザーとしてログイン**:
   - クイックログインボタン「ユーザー」をクリック
   - または、ユーザー名: `user`、パスワード: `user`

### 主な機能

#### ダッシュボード（全ユーザー）
- AIモデルの選択
- チャット機能
- 設定変更（テーマ、フォントサイズなど）

#### 管理者画面（管理者のみ）
1. **ユーザー管理**
   - ユーザーの追加・編集・削除
   - パスワード変更

2. **AIモデル管理**
   - 利用可能なモデルの表示
   - モデルの有効化/無効化
   - GPU対応状況の確認

3. **NAS設定**
   - NAS接続の追加・編集
   - マウント/アンマウント
   - 接続状態の監視

4. **ネットワーク設定**
   - ホスト名、IPアドレス設定
   - ポート設定
   - SSL/TLS設定

## 📦 検出されたAIモデル

現在、以下のモデルが検出されています：
1. Qwen2.5 Coder 7B Instruct Q4_K_M
2. Qwen2 1.5B Instruct Q8_0
3. Nomic Embed Text V1.5.F16

## 🔧 次のステップ

### Python依存関係のインストール（LLM機能を有効にする場合）

```bash
# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

**GPU対応の場合**:

**NVIDIA GPU (CUDA)**:
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

**Intel GPU (OpenCL)**:
```bash
CMAKE_ARGS="-DLLAMA_CLBLAST=on" pip install llama-cpp-python
```

### 本番環境へのデプロイ

```bash
# Next.jsアプリケーションのビルド
npm run build

# 本番サーバーの起動
npm start
```

## 🎨 UIの特徴

- **グラスモーフィズムデザイン**: 半透明の美しいカード
- **グラデーション**: 鮮やかなインディゴ〜ピンクのグラデーション
- **スムーズアニメーション**: フェードイン、スライドインなど
- **レスポンシブ**: PC、タブレット、スマートフォン対応
- **ダークモード**: 目に優しいダークテーマ

## 📁 プロジェクト構造

```
on-premises-llm/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── admin/        # 管理者画面
│   │   ├── dashboard/    # ダッシュボード
│   │   ├── api/          # APIルート
│   │   └── page.tsx      # ログイン画面
│   ├── components/       # Reactコンポーネント
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── AdminPage.tsx
│   │   └── SettingsModal.tsx
│   ├── lib/              # コンテキストとユーティリティ
│   │   ├── auth-context.tsx
│   │   └── settings-context.tsx
│   └── types/            # TypeScript型定義
├── models/               # AIモデル（GGUF形式）
├── mnt/                  # NASマウントポイント
├── chat_histories/       # チャット履歴
├── backend.py            # Pythonバックエンド
├── requirements.txt      # Python依存関係
└── package.json          # Node.js依存関係
```

## 🔐 セキュリティ注意事項

- 本番環境では、必ず強力なパスワードを設定してください
- SSL/TLSを有効にしてください
- ファイアウォールを適切に設定してください
- 定期的にバックアップを取ってください

## 📞 サポート

問題が発生した場合は、以下を確認してください：
1. Node.jsとPythonのバージョン
2. 依存関係が正しくインストールされているか
3. ポート3000が使用可能か
4. ブラウザのコンソールにエラーがないか

---

**Oonanji Vault** へようこそ！🎉
