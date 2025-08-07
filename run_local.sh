#!/bin/bash

# メルマガ「一日一知」生成システム - ローカル実行スクリプト

echo "🚀 メルマガ生成システムを起動中..."

# 仮想環境を有効化
echo "📦 仮想環境を有効化中..."
source env/bin/activate

# Streamlitアプリを起動
echo "🌐 Streamlitアプリを起動中..."
echo "📍 URL: http://localhost:8501"
echo ""
echo "⏹️  停止するには Ctrl+C を押してください"
echo ""

streamlit run streamlit_app.py