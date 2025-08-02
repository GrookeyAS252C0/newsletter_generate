# 推奨コマンド

## 基本開発コマンド

### アプリケーション起動
```bash
streamlit run main.py
```

### 環境構築
```bash
# 仮想環境作成（推奨）
python -m venv env
source env/bin/activate  # macOS/Linux
# env\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### テスト実行
```bash
# RAGシステムのテスト
python test_rag_system.py
```

## Git操作
```bash
git status
git add .
git commit -m "メッセージ"
git push
```

## システム固有コマンド（Darwin/macOS）
```bash
# ファイル検索
find . -name "*.py" -type f

# プロセス確認
ps aux | grep python

# ポート確認
lsof -i :8501  # Streamlitデフォルトポート
```

## 環境変数設定
```bash
# .envファイル作成
touch .env

# 必要な環境変数
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "YOUTUBE_API_KEY=your_key_here" >> .env
```

## プロジェクト構造確認
```bash
# ディレクトリ構造表示
tree -I '__pycache__|*.pyc|env'

# ファイル一覧
ls -la
```

## 注意：設定・テスト・リントコマンドについて
- 現在のプロジェクトには公式のテスト・リント・フォーマット設定は存在しない
- test_rag_system.pyが唯一のテストファイル  
- 本格的な開発時は pytest, black, flake8 等の導入を検討