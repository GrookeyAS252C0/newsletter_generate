# メルマガ「一日一知」生成システム

日本大学第一中学・高等学校向けメールマガジン自動生成アプリケーション

## 概要

このシステムは、学校の広報活動を支援するために開発されたメールマガジン自動生成ツールです。天気予報、学校行事、説明会情報、YouTube動画などを統合し、毎日配信するメールマガジン「一日一知」を自動生成します。

## 主な機能

- 📅 **学校行事管理**: Google CalendarまたはCSVファイルから行事情報を取得
- 🌤️ **天気予報取得**: 墨田区の天気情報を複数のソースから取得・統合
- 🎉 **イベント情報管理**: 学校説明会等の広報イベント情報を管理
- 📺 **YouTube連携**: 公式チャンネルの動画を検索し、字幕から要約・キャッチコピーを自動生成
- 📧 **メルマガ自動生成**: 上記情報を統合してテンプレートに基づくメールマガジンを作成

## 技術スタック

- **フロントエンド**: Streamlit
- **AI/言語処理**: OpenAI API, LangChain
- **外部API**: Google Calendar API, YouTube Data API
- **データ処理**: pandas, Jinja2

## セットアップ

### 1. 必要な環境

- Python 3.8以上
- pip

### 2. インストール

```bash
# リポジトリのクローン
git clone [repository-url]
cd DMM_OptionalAssignment20250608

# 仮想環境の作成（推奨）
python -m venv env
source env/bin/activate  # Windowsの場合: env\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

#### ローカル環境の場合

`.env`ファイルをプロジェクトルートに作成し、以下の内容を記載：

```
OPENAI_API_KEY=your_openai_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

#### Streamlit Cloudの場合

1. Streamlit Cloudのダッシュボードにアクセス
2. アプリの設定画面を開く
3. 「Secrets」セクションで以下を追加：

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
YOUTUBE_API_KEY = "your_youtube_api_key_here"

# Google Calendar APIを使用する場合（オプション）
# credentials.jsonの内容をJSON文字列として追加
GOOGLE_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''
```

### 4. Google Calendar設定（オプション）

Google Calendar APIを使用する場合：

1. Google Cloud Consoleでプロジェクトを作成
2. Calendar APIを有効化
3. OAuth2認証情報を作成
4. `credentials.json`をダウンロードしてプロジェクトルートに配置

## 使用方法

```bash
# アプリケーションの起動
streamlit run main.py
```

ブラウザが自動的に開き、アプリケーションが表示されます。

### 基本的な操作

1. **発行日の選択**: サイドバーで発行日を選択
2. **カレンダー設定**: 使用するGoogle Calendarを選択（オプション）
3. **メルマガ生成**: 「メルマガを生成」ボタンをクリック
4. **結果の確認**: 生成されたメルマガをプレビュー
5. **ダウンロード**: TXTまたはMD形式でダウンロード

## プロジェクト構成

```
DMM_OptionalAssignment20250608/
├── main.py                    # エントリーポイント
├── ui.py                      # Streamlit UI管理
├── newsletter_generator.py    # メルマガ生成ロジック
├── config.py                  # 設定とデータクラス
├── calendar_service.py        # Google Calendar連携
├── weather_service.py         # 天気情報取得
├── youtube_service.py         # YouTube API連携
├── data_loader.py            # イベントデータ管理
├── utils.py                  # ユーティリティ関数
├── web_loader.py             # Web情報取得
├── requirements.txt          # 依存関係
├── data/                     # データファイル
│   ├── event2025.csv
│   └── schedule2025.csv
└── .env                      # 環境変数（要作成）
```

## ライセンス

このプロジェクトは教育目的で作成されています。

## 注意事項

- APIキーは絶対に公開しないでください
- `credentials.json`と`token.json`はGitにコミットしないでください
- 天気予報データの利用には各サービスの利用規約を確認してください