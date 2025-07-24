"""
健康知識RAGシステム
Deep Researchで得られた医学的知見を活用した体調管理メッセージ生成
"""

import json
import os
import random
from typing import Dict, List, Any, Optional
from datetime import date

try:
    import streamlit as st
except ImportError:
    class DummySt:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    st = DummySt()

from config import WeatherInfo


class HealthKnowledgeRAG:
    """Deep Research結果を活用した健康知識RAGシステム"""
    
    def __init__(self, knowledge_json_path: str = "condition_clean.json"):
        """
        RAGシステムを初期化
        
        Args:
            knowledge_json_path: Deep Research結果のJSONファイルパス
        """
        self.knowledge_path = knowledge_json_path
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """知識ベースをJSONファイルから読み込み"""
        try:
            if not os.path.exists(self.knowledge_path):
                st.error(f"知識ベースファイルが見つかりません: {self.knowledge_path}")
                return {}
                
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
                st.info(f"✅ 知識ベース読み込み完了: {self.knowledge_path}")
                return knowledge
                
        except json.JSONDecodeError as e:
            st.error(f"JSONファイルの解析に失敗: {e}")
            return {}
        except Exception as e:
            st.error(f"知識ベースの読み込みに失敗: {e}")
            return {}
    
    def get_pressure_advice(self, pressure_status: str) -> Dict[str, Any]:
        """気圧状況に基づく体調管理アドバイスを取得"""
        if not self.knowledge_base:
            return {}
            
        try:
            pressure_effects = self.knowledge_base.get("atmospheric_pressure_effects", {})
            
            # 低気圧の場合の詳細情報を取得
            if "低気圧" in pressure_status:
                return {
                    "mechanisms": pressure_effects.get("physiological_mechanisms", {}),
                    "symptoms": pressure_effects.get("symptoms_and_conditions", {}).get("low_pressure_symptoms", {}),
                    "prevention": pressure_effects.get("prevention_and_management", {}),
                    "evidence_level": pressure_effects.get("research_metadata", {}).get("evidence_level", "中"),
                    "advice_type": "low_pressure"
                }
            # 高気圧の場合
            elif "高気圧" in pressure_status:
                return {
                    "effects": pressure_effects.get("symptoms_and_conditions", {}).get("high_pressure_symptoms", {}),
                    "prevention": pressure_effects.get("prevention_and_management", {}),
                    "evidence_level": pressure_effects.get("research_metadata", {}).get("evidence_level", "中"),
                    "advice_type": "high_pressure"
                }
            else:
                # その他の気圧状況
                return {
                    "general_effects": pressure_effects.get("symptoms_and_conditions", {}),
                    "prevention": pressure_effects.get("prevention_and_management", {}),
                    "evidence_level": "中",
                    "advice_type": "general_pressure"
                }
                
        except Exception as e:
            st.warning(f"気圧アドバイス取得エラー: {e}")
            return {}
    
    def get_lunar_advice(self, lunar_phase: str) -> Dict[str, Any]:
        """月齢に基づく体調管理アドバイスを取得"""
        if not self.knowledge_base:
            return {}
            
        try:
            lunar_effects = self.knowledge_base.get("lunar_phase_effects", {})
            
            # 新月の場合
            if "新月" in lunar_phase:
                return {
                    "phase_effects": lunar_effects.get("phase_specific_effects", {}).get("new_moon", {}),
                    "wellness_practices": lunar_effects.get("practical_applications", {}).get("wellness_practices", {}).get("new_moon_recommendations", ""),
                    "evidence_level": lunar_effects.get("research_metadata", {}).get("evidence_level", "低"),
                    "advice_type": "new_moon"
                }
            # 満月の場合
            elif "満月" in lunar_phase:
                return {
                    "phase_effects": lunar_effects.get("phase_specific_effects", {}).get("full_moon", {}),
                    "wellness_practices": lunar_effects.get("practical_applications", {}).get("wellness_practices", {}).get("full_moon_recommendations", ""),
                    "evidence_level": lunar_effects.get("research_metadata", {}).get("evidence_level", "低"),
                    "advice_type": "full_moon"
                }
            # 上弦の月
            elif "上弦" in lunar_phase or "まで" in lunar_phase:
                return {
                    "phase_effects": lunar_effects.get("phase_specific_effects", {}).get("waxing_moon", {}),
                    "evidence_level": "低",
                    "advice_type": "waxing_moon"
                }
            # 下弦の月
            else:
                return {
                    "phase_effects": lunar_effects.get("phase_specific_effects", {}).get("waning_moon", {}),
                    "evidence_level": "低",
                    "advice_type": "waning_moon"
                }
                
        except Exception as e:
            st.warning(f"月齢アドバイス取得エラー: {e}")
            return {}
    
    def get_integration_guidelines(self) -> Dict[str, Any]:
        """統合ガイドラインを取得"""
        if not self.knowledge_base:
            return {}
            
        return self.knowledge_base.get("integration_guidelines", {})
    
    def generate_evidence_based_message(self, weather_info: WeatherInfo, target_date: date) -> str:
        """RAGシステムを使用してエビデンスベースのメッセージを生成"""
        try:
            # 気圧と月齢の情報を取得
            pressure_advice = self.get_pressure_advice(weather_info.気圧状況)
            lunar_advice = self.get_lunar_advice(weather_info.月齢)
            guidelines = self.get_integration_guidelines()
            
            # メッセージ生成ルールを取得
            message_rules = guidelines.get("message_generation_rules", {})
            advice_framework = guidelines.get("practical_advice_framework", {})
            
            # エビデンスレベルに基づく表現を決定
            pressure_expression = self._get_expression_by_evidence(
                pressure_advice.get("evidence_level", "中")
            )
            lunar_expression = self._get_expression_by_evidence(
                lunar_advice.get("evidence_level", "低")
            )
            
            # バリエーション豊かなメッセージ視点を選択
            perspective = self._select_message_perspective()
            
            # 具体的なアドバイスを構築
            pressure_content = self._build_pressure_content(pressure_advice, pressure_expression)
            lunar_content = self._build_lunar_content(lunar_advice, lunar_expression)
            practical_advice = self._build_practical_advice(pressure_advice, lunar_advice, advice_framework)
            
            # 統合メッセージを構築
            formatted_date = f"{target_date.month}月{target_date.day}日"
            
            # 降水確率チェック
            rain_advice = ""
            if weather_info.降水確率 and any(char.isdigit() for char in weather_info.降水確率):
                import re
                numbers = re.findall(r'\d+', weather_info.降水確率)
                if numbers and int(numbers[0]) >= 50:
                    rain_advice = "傘をお忘れなくお持ちください。"
            
            message = self._construct_final_message(
                formatted_date, weather_info.快適具合, pressure_content, 
                lunar_content, practical_advice, rain_advice, perspective
            )
            
            return message
            
        except Exception as e:
            st.error(f"RAGメッセージ生成エラー: {e}")
            return self._generate_fallback_message(weather_info)
    
    def _get_expression_by_evidence(self, evidence_level: str) -> Dict[str, str]:
        """エビデンスレベルに応じた表現パターンを取得"""
        expressions = {
            "高": {
                "certainty": "研究により確認されています",
                "recommendation": "をお勧めします", 
                "effect": "効果があります",
                "condition": "ことが知られています",
                "advice": "ことが大切です"
            },
            "中": {
                "certainty": "効果が期待されます",
                "recommendation": "を試してみてはいかがでしょう",
                "effect": "役立つ可能性があります",
                "condition": "と考えられています",
                "advice": "ことをお勧めします"
            },
            "低": {
                "certainty": "と言われています",
                "recommendation": "という方法もあります",
                "effect": "かもしれません",
                "condition": "とされています",
                "advice": "ことも一つの方法です"
            }
        }
        return expressions.get(evidence_level, expressions["中"])
    
    def _select_message_perspective(self) -> str:
        """メッセージの視点をランダムに選択"""
        perspectives = [
            "preventive_care",  # 予防的ケア
            "body_care",        # 体のケア  
            "mental_care",      # 心のケア
            "traditional",      # 東洋医学的
            "scientific",       # 現代医学的
            "seasonal"          # 季節感重視
        ]
        return random.choice(perspectives)
    
    def _build_pressure_content(self, pressure_advice: Dict[str, Any], expression: Dict[str, str]) -> str:
        """気圧関連コンテンツを構築（エビデンスレベル別表現制御）"""
        if not pressure_advice:
            return ""
            
        advice_type = pressure_advice.get("advice_type", "")
        evidence_level = pressure_advice.get("evidence_level", "中")
        
        if advice_type == "low_pressure":
            symptoms = pressure_advice.get("symptoms", {}).get("primary_symptoms", [])
            if symptoms:
                symptom_text = "、".join(symptoms[:2])
                if evidence_level == "高":
                    return f"低気圧により{symptom_text}が生じやすい{expression['condition']}。"
                else:
                    return f"低気圧の影響で{symptom_text}を感じる方もいらっしゃいます。"
            else:
                return f"低気圧による体調への影響{expression['condition']}。"
                
        elif advice_type == "high_pressure":
            if evidence_level == "高":
                return f"高気圧に覆われ自律神経も安定しやすい{expression['condition']}。"
            else:
                return "高気圧により比較的穏やかな気候となっています。"
                
        else:
            return f"気圧変化による体調への影響{expression['condition']}。"
    
    def _build_lunar_content(self, lunar_advice: Dict[str, Any], expression: Dict[str, str]) -> str:
        """月齢関連コンテンツを構築（エビデンスレベル別表現制御）"""
        if not lunar_advice:
            return ""
            
        advice_type = lunar_advice.get("advice_type", "")
        evidence_level = lunar_advice.get("evidence_level", "低")
        
        # 月齢は基本的にエビデンスレベルが低いため、控えめな表現を使用
        if advice_type == "new_moon":
            if evidence_level == "低":
                return "新月の時期は心身のリセットに適しているとされています。"
            else:
                return f"新月の時期は体内リズムの調整{expression['condition']}。"
                
        elif advice_type == "full_moon":
            if evidence_level == "低":
                return "満月前後は一部の方で睡眠への影響を感じることがあります。"
            else:
                return f"満月時期の睡眠への影響{expression['condition']}。"
                
        elif advice_type == "waxing_moon":
            return "月が満ちる時期はエネルギーが高まるとされています。"
            
        else:
            return f"月の満ち欠けのリズムを意識した生活{expression['advice']}。"
    
    def _build_practical_advice(self, pressure_advice: Dict[str, Any], 
                              lunar_advice: Dict[str, Any], 
                              advice_framework: Dict[str, Any]) -> str:
        """実践的アドバイスを構築（エビデンスレベル別）"""
        advice_parts = []
        
        # 気圧対策（エビデンス高）
        if pressure_advice.get("advice_type") == "low_pressure":
            prevention = pressure_advice.get("prevention", {})
            ear_massage = prevention.get("evidence_based_methods", {}).get("ear_massage", {})
            evidence_level = pressure_advice.get("evidence_level", "中")
            
            if ear_massage:
                if evidence_level == "高":
                    advice_parts.append("耳のマッサージで内耳の血流を促進し")
                else:
                    advice_parts.append("耳のマッサージなどのケアで")
        
        # 月齢対策（エビデンス低）- 控えめに提案
        lunar_type = lunar_advice.get("advice_type", "")
        lunar_evidence = lunar_advice.get("evidence_level", "低")
        
        if lunar_type == "new_moon" and lunar_evidence == "低":
            advice_parts.append("水分補給を心がけて")
        elif lunar_type == "full_moon" and lunar_evidence == "低":
            advice_parts.append("質の良い睡眠を意識して")
            
        # 基本的な体調管理（常に含める）
        if advice_parts:
            advice_parts.append("体調管理にお気をつけください")
        else:
            advice_parts.append("日々の体調管理を大切にお過ごしください")
        
        return "、".join(advice_parts) + "。"
    
    def _construct_final_message(self, formatted_date: str, comfort_level: str,
                               pressure_content: str, lunar_content: str, 
                               practical_advice: str, rain_advice: str, 
                               perspective: str) -> str:
        """最終メッセージを構築"""
        
        # 快適具合による導入
        comfort_intro = f"本日は{comfort_level}一日となる予想です。"
        
        # メッセージ要素を統合
        message_parts = [comfort_intro]
        
        if pressure_content:
            message_parts.append(pressure_content)
            
        if lunar_content:
            message_parts.append(lunar_content)
            
        if practical_advice:
            message_parts.append(practical_advice)
            
        if rain_advice:
            message_parts.append(rain_advice)
            
        # 締めくくり
        message_parts.append("受験生の皆様も保護者の方々も、どうぞお体を大切にお過ごしください。")
        
        return "".join(message_parts)
    
    def _generate_fallback_message(self, weather_info: WeatherInfo) -> str:
        """フォールバックメッセージを生成"""
        return f"本日は{weather_info.快適具合}一日となる予想です。{weather_info.月齢}の時期で{weather_info.気圧状況}の影響もございますので、体調管理にお気をつけください。"


class MessageVariationManager:
    """メッセージバリエーション管理クラス"""
    
    def __init__(self):
        self.used_patterns = []
        self.max_history = 10  # 直近10パターンを記憶
    
    def get_unique_perspective(self) -> str:
        """重複しない視点を選択"""
        all_perspectives = [
            "preventive_care", "body_care", "mental_care", 
            "traditional", "scientific", "seasonal"
        ]
        
        # 未使用の視点を優先
        available = [p for p in all_perspectives if p not in self.used_patterns[-3:]]
        if not available:
            available = all_perspectives
            
        selected = random.choice(available)
        
        # 履歴を更新
        self.used_patterns.append(selected)
        if len(self.used_patterns) > self.max_history:
            self.used_patterns.pop(0)
            
        return selected
    
    def reset_patterns(self):
        """パターン履歴をリセット"""
        self.used_patterns = []