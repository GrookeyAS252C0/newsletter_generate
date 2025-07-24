"""
RAGシステムのテスト実行
"""

import os
import sys
from datetime import date
from dataclasses import dataclass

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# テスト用の設定クラス
@dataclass
class TestWeatherInfo:
    天気概況: str
    気温: str  
    湿度: str
    風速: str
    降水確率: str
    快適具合: str
    月齢: str
    気圧状況: str


def test_rag_system():
    """RAGシステムの動作テスト"""
    print("🧪 RAGシステムのテスト開始")
    
    try:
        # RAGシステムをインポート
        from health_knowledge_rag import HealthKnowledgeRAG
        
        # テストケース1: 低気圧 + 新月
        print("\n📋 テストケース1: 低気圧 + 新月")
        test_weather_1 = TestWeatherInfo(
            天気概況="曇り",
            気温="最高気温25度、最低気温18度",
            湿度="65%",
            風速="北風2m/s",
            降水確率="午前30%、午後40%",
            快適具合="やや蒸し暑い",
            月齢="今日が新月",
            気圧状況="低気圧の影響"
        )
        
        rag_system = HealthKnowledgeRAG()
        message_1 = rag_system.generate_evidence_based_message(test_weather_1, date.today())
        print(f"生成メッセージ: {message_1}")
        
        # テストケース2: 高気圧 + 満月
        print("\n📋 テストケース2: 高気圧 + 満月")
        test_weather_2 = TestWeatherInfo(
            天気概況="晴れ",
            気温="最高気温22度、最低気温15度",
            湿度="45%",
            風速="南風1m/s",
            降水確率="午前10%、午後20%",
            快適具合="過ごしやすい",
            月齢="明日が満月",
            気圧状況="高気圧に覆われる"
        )
        
        message_2 = rag_system.generate_evidence_based_message(test_weather_2, date.today())
        print(f"生成メッセージ: {message_2}")
        
        # テストケース3: 気圧の谷 + 満月まであと3日
        print("\n📋 テストケース3: 気圧の谷 + 満月まであと3日")
        test_weather_3 = TestWeatherInfo(
            天気概況="雨",
            気温="最高気温28度、最低気温22度",
            湿度="85%",
            風速="東風3m/s",
            降水確率="午前70%、午後60%",
            快適具合="蒸し暑い",
            月齢="満月まであと3日",
            気圧状況="気圧の谷の影響"
        )
        
        message_3 = rag_system.generate_evidence_based_message(test_weather_3, date.today())
        print(f"生成メッセージ: {message_3}")
        
        # RAGシステムの各コンポーネントのテスト
        print("\n🔍 RAGシステムコンポーネントテスト")
        
        # 気圧アドバイステスト
        pressure_advice = rag_system.get_pressure_advice("低気圧の影響")
        print(f"気圧アドバイス: {pressure_advice.get('advice_type', 'N/A')}")
        
        # 月齢アドバイステスト
        lunar_advice = rag_system.get_lunar_advice("今日が満月")
        print(f"月齢アドバイス: {lunar_advice.get('advice_type', 'N/A')}")
        
        # 統合ガイドラインテスト
        guidelines = rag_system.get_integration_guidelines()
        print(f"統合ガイドライン取得: {'✅' if guidelines else '❌'}")
        
        print("\n✅ RAGシステムテスト完了")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False


def test_weather_service_integration():
    """WeatherServiceとRAGシステムの統合テスト"""
    print("\n🔗 WeatherService統合テスト開始")
    
    try:
        from weather_service import WeatherService
        from config import WeatherInfo
        
        # テスト用のAPIキー（ダミー）
        weather_service = WeatherService("test-api-key")
        
        # テスト用WeatherInfoオブジェクト
        test_weather = WeatherInfo(
            天気概況="曇り",
            気温="最高気温24度、最低気温17度",
            湿度="70%", 
            風速="北東風2m/s",
            降水確率="午前40%、午後50%",
            快適具合="やや肌寒い",
            月齢="新月まであと2日",
            気圧状況="低気圧接近中"
        )
        
        # メッセージ生成テスト（RAGシステム経由）
        print("RAGシステム経由でのメッセージ生成テスト...")
        message = weather_service.generate_heartwarming_message(test_weather, date.today())
        print(f"統合メッセージ: {message}")
        
        print("✅ WeatherService統合テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False


def check_knowledge_base():
    """知識ベースファイルの存在確認"""
    print("\n📚 知識ベースファイル確認")
    
    knowledge_file = "condition_clean.json"
    if os.path.exists(knowledge_file):
        print(f"✅ 知識ベースファイル確認: {knowledge_file}")
        
        # ファイルサイズ確認
        file_size = os.path.getsize(knowledge_file)
        print(f"ファイルサイズ: {file_size:,} bytes")
        
        # JSON形式の確認
        try:
            import json
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"JSONパース: ✅")
            print(f"メインキー: {list(data.keys())}")
            
            # 気圧情報の存在確認
            if "atmospheric_pressure_effects" in data:
                print("✅ 気圧関連データ存在")
            else:
                print("❌ 気圧関連データ不在")
                
            # 月齢情報の存在確認  
            if "lunar_phase_effects" in data:
                print("✅ 月齢関連データ存在")
            else:
                print("❌ 月齢関連データ不在")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析エラー: {e}")
            return False
    else:
        print(f"❌ 知識ベースファイルが見つかりません: {knowledge_file}")
        return False


if __name__ == "__main__":
    print("🚀 RAGシステム総合テスト開始")
    
    # 知識ベースファイル確認
    kb_ok = check_knowledge_base()
    
    if kb_ok:
        # RAGシステム単体テスト
        rag_ok = test_rag_system()
        
        if rag_ok:
            # 統合テスト
            integration_ok = test_weather_service_integration()
            
            if integration_ok:
                print("\n🎉 全テスト成功！RAGシステムが正常に動作しています。")
            else:
                print("\n⚠️ 統合テストで問題が発生しました。")
        else:
            print("\n⚠️ RAGシステム単体テストで問題が発生しました。")
    else:
        print("\n⚠️ 知識ベースファイルの問題により、テストを実行できません。")
    
    print("\n📊 テスト実行完了")