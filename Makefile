# メルマガ生成システム - 開発用Makefile

.PHONY: help install install-dev test test-verbose lint format typecheck clean run run-improved setup

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  make install      - 本番用依存関係をインストール"
	@echo "  make install-dev  - 開発用依存関係もインストール"
	@echo "  make test         - テストを実行"
	@echo "  make test-verbose - 詳細なテスト実行"
	@echo "  make lint         - コードリント（flake8）"
	@echo "  make format       - コードフォーマット（black）"
	@echo "  make typecheck    - 型チェック（mypy）"
	@echo "  make clean        - キャッシュファイルを削除"
	@echo "  make run          - アプリケーションを起動"
	@echo "  make setup        - 初回セットアップ"

# 依存関係のインストール
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest black flake8 mypy coverage

# テスト実行
test:
	python -m pytest tests/ -v

test-verbose:
	python -m pytest tests/ -v --tb=long --cov=src --cov-report=term-missing

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html

# コード品質チェック
lint:
	python -m flake8 src/ tests/ --exclude=src/ui/__pycache__,src/core/__pycache__,src/utils/__pycache__

format:
	python -m black src/ tests/ streamlit_app.py

format-check:
	python -m black --check src/ tests/ streamlit_app.py

typecheck:
	python -m mypy src/ --ignore-missing-imports

# すべての品質チェックを実行
quality: format-check lint typecheck test

# キャッシュ削除
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf .cache/ logs/ 2>/dev/null || true

# アプリケーション起動
run:
	streamlit run streamlit_app.py

# 開発環境セットアップ
setup: install-dev
	@echo "開発環境のセットアップ完了"
	@echo ""
	@echo "次のステップ:"
	@echo "1. .envファイルを作成してAPIキーを設定"
	@echo "2. make run でアプリケーションを起動"
	@echo "3. make test でテストを実行"

# CI/CD用のターゲット
ci: clean install-dev quality
	@echo "CI/CDパイプライン完了"

# パフォーマンステスト用
test-performance:
	python -m pytest tests/ -m "not slow" --tb=short

# セキュリティチェック（banditが必要）
security:
	@echo "セキュリティチェックを実行するには 'pip install bandit' を実行してください"
	# bandit -r src/ -f json -o security-report.json || true