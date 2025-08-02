# タスク完了時のチェックリスト

## コード変更後の必須確認項目

### 1. 基本動作確認
```bash
# アプリケーション起動テスト
streamlit run main.py
```

### 2. テスト実行
```bash
# RAGシステムテスト
python test_rag_system.py
```

### 3. 依存関係チェック
```bash
# 新しいライブラリを追加した場合
pip freeze > requirements.txt
```

### 4. 環境変数確認
- `.env`ファイルの設定が正しいか確認
- `OPENAI_API_KEY`, `YOUTUBE_API_KEY`等の必要な環境変数が設定されているか

### 5. エラーハンドリング確認
- 外部API（OpenAI, YouTube, Google Calendar）の呼び出し部分
- フォールバック機能が正常に動作するか

### 6. ファイル・データの整合性
- `data/`ディレクトリ内のCSVファイル
- JSON設定ファイル（pressure_impact_data.json等）

## 現在利用できないツール
⚠️ **注意**: 以下のツールは現在プロジェクトに設定されていません
- **リント**: flake8, pylint等
- **フォーマット**: black, autopep8等  
- **型チェック**: mypy等
- **本格的テスト**: pytest等

## 推奨追加設定（将来的）
```bash
# 開発ツール導入例
pip install pytest black flake8 mypy
```

## Git管理
```bash
# 変更確認
git status
git diff

# コミット前の最終確認
git add .
git commit -m "変更内容の説明"
```