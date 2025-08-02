# コードスタイル・規約

## ファイル構成
- **エントリーポイント**: main.py
- **モジュール別ファイル**: 機能ごとに分離（ui.py, config.py, utils.py等）
- **データファイル**: data/ディレクトリに配置

## コーディング規約

### 型ヒント
- **必須**: 全ての関数・メソッドで型ヒントを使用
- **import**: `from typing import Dict, List, Any, Optional`
- **例**: `def get_japanese_weekday(date_obj: date) -> str:`

### docstring
- **形式**: トリプルクォート `"""`
- **言語**: 日本語
- **例**: `"""日付から日本語の曜日（フル）を取得"""`

### クラス設計
- **dataclass使用**: 設定・データクラスは `@dataclass` デコレータ
- **静的メソッド**: ユーティリティ関数は `@staticmethod`
- **命名**: PascalCase（例: `DateUtils`, `AppConfig`）

### 変数・関数命名
- **関数**: snake_case（例: `get_japanese_weekday`）
- **定数**: 大文字（例: `USER_AGENT`）
- **プライベート**: アンダースコア接頭辞（例: `_get_school_context`）

### インポート順序
1. 標準ライブラリ
2. サードパーティライブラリ  
3. 自作モジュール

### エラーハンドリング
- **必須**: 外部API呼び出しは try-except
- **フォールバック**: 複数段階のフォールバック機能
- **ユーザビリティ**: Streamlitでのエラー表示