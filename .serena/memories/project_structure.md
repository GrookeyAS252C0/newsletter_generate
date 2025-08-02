# プロジェクト構造

## ディレクトリ構成
```
DMM_OptionalAssignment20250608/
├── main.py                    # エントリーポイント（Streamlit起動）
├── ui.py                      # Streamlit UI管理
├── newsletter_generator.py    # メルマガ生成ロジック
├── config.py                  # 設定とデータクラス
├── calendar_service.py        # Google Calendar連携
├── weather_service.py         # 天気情報取得
├── youtube_service.py         # YouTube API連携
├── data_loader.py            # イベントデータ管理
├── utils.py                  # ユーティリティ関数
├── web_loader.py             # Web情報取得
├── health_knowledge_rag.py   # RAGシステム（健康アドバイス）
├── test_rag_system.py        # RAGシステムテスト
├── requirements.txt          # 依存関係
├── README.md                 # プロジェクト説明
├── DEVELOPMENT_ROADMAP.md    # 開発ロードマップ
├── data/                     # データファイル
│   ├── event2025.csv         # イベント情報
│   └── schedule2025.csv      # スケジュール情報
├── .serena/                  # Serena設定
├── .claude/                  # Claude設定  
├── .devcontainer/            # 開発コンテナ設定
└── .env                      # 環境変数（要作成）
```

## 主要コンポーネント

### コア機能
- **main.py**: アプリケーションエントリーポイント
- **ui.py**: Streamlitベースのユーザーインターフェース
- **newsletter_generator.py**: メルマガ生成の中核ロジック

### データ処理
- **weather_service.py**: 天気情報取得・気圧/月齢分析
- **calendar_service.py**: Google Calendar連携
- **youtube_service.py**: YouTube動画情報取得
- **data_loader.py**: CSV/イベントデータ管理

### AI・知識ベース
- **health_knowledge_rag.py**: RAGシステム、健康アドバイス生成

### ユーティリティ
- **config.py**: アプリケーション設定管理
- **utils.py**: 日付処理等の共通関数
- **web_loader.py**: Web情報取得