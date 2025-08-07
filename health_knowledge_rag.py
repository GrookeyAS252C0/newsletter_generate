"""
健康知識RAGシステム
Deep Researchで得られた医学的知見を活用した体調管理メッセージ生成
"""

import json
import os
import random
import time
from typing import Dict, List, Any, Optional
from datetime import date
import openai

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
    
    def __init__(self, knowledge_json_path: str = "condition_clean.json", openai_client = None):
        """
        RAGシステムを初期化
        
        Args:
            knowledge_json_path: Deep Research結果のJSONファイルパス
            openai_client: OpenAI APIクライアント（LLM月齢コメント生成用）
        """
        self.knowledge_path = knowledge_json_path
        self.knowledge_base = self._load_knowledge_base()
        self.openai_client = openai_client
        
        # 新しい気圧・月齢影響データを読み込み
        self.pressure_data = self._load_specialized_data("pressure_impact_data.json")
        self.lunar_data = self._load_specialized_data("lunar_impact_data.json")
        
        # 学校紹介機能は削除済み
        
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
    
    def _load_specialized_data(self, file_path: str) -> Dict[str, Any]:
        """専用の気圧・月齢データファイルを読み込み"""
        try:
            if not os.path.exists(file_path):
                st.warning(f"専用データファイルが見つかりません: {file_path}")
                return {}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.info(f"✅ 専用データ読み込み完了: {file_path}")
                return data
                
        except json.JSONDecodeError as e:
            st.error(f"専用データファイルの解析に失敗: {e}")
            return {}
        except Exception as e:
            st.error(f"専用データの読み込みに失敗: {e}")
            return {}
    
    def get_pressure_advice(self, pressure_status: str) -> Dict[str, Any]:
        """気圧状況に基づく体調管理アドバイスを取得（既存メソッド）"""
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
    
    def get_specialized_pressure_advice(self, pressure_status: str) -> Dict[str, Any]:
        """新しい専用データから気圧影響のアドバイスを取得"""
        if not self.pressure_data:
            return self.get_pressure_advice(pressure_status)  # フォールバック
            
        try:
            conditions = self.pressure_data.get("pressure_conditions", {})
            
            # 気圧状況に応じたデータを取得
            if "低気圧" in pressure_status:
                return conditions.get("low_pressure", {})
            elif "高気圧" in pressure_status:
                return conditions.get("high_pressure", {})
            elif "変化" in pressure_status or "谷" in pressure_status:
                return conditions.get("pressure_change", {})
            else:
                # デフォルトは低気圧として扱う
                return conditions.get("low_pressure", {})
                
        except Exception as e:
            st.warning(f"専用気圧アドバイス取得エラー: {e}")
            return self.get_pressure_advice(pressure_status)
    
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
    
    def get_specialized_lunar_advice(self, lunar_phase: str) -> Dict[str, Any]:
        """新しい専用データから月齢影響のアドバイスを取得"""
        if not self.lunar_data:
            return self.get_lunar_advice(lunar_phase)  # フォールバック
            
        try:
            phases = self.lunar_data.get("lunar_phases", {})
            
            # 月相に応じたデータを取得
            if "新月" in lunar_phase:
                return phases.get("new_moon", {})
            elif "満月" in lunar_phase:
                return phases.get("full_moon", {})
            elif "上弦" in lunar_phase or "まで" in lunar_phase or "三日月" in lunar_phase:
                return phases.get("waxing_moon", {})
            elif "下弦" in lunar_phase or "二十六夜" in lunar_phase:
                return phases.get("waning_moon", {})
            else:
                # デフォルトは新月として扱う
                return phases.get("new_moon", {})
                
        except Exception as e:
            st.warning(f"専用月齢アドバイス取得エラー: {e}")
            return self.get_lunar_advice(lunar_phase)
    
    def get_precise_lunar_data(self, lunar_phase_text: str, moon_age: Optional[float] = None) -> Dict[str, Any]:
        """月齢数値と説明文から正確な月相を判定"""
        if moon_age is None:
            # 月齢数値が取得できない場合は従来の判定
            return {"use_traditional": True, "phase_text": lunar_phase_text}
        
        try:
            # 月齢を0-29.5の範囲に正規化
            normalized_age = moon_age % 29.5
            
            # 主影響と副影響を判定
            primary_influence = self._determine_primary_influence(normalized_age)
            secondary_influence = self._determine_secondary_influence(normalized_age)
            influence_strength = self._calculate_influence_strength(normalized_age)
            
            return {
                "moon_age": normalized_age,
                "phase_text": lunar_phase_text,
                "primary_influence": primary_influence,
                "secondary_influence": secondary_influence,
                "influence_strength": influence_strength,
                "phase_description": self._get_detailed_phase_description(normalized_age),
                "use_traditional": False
            }
            
        except Exception as e:
            st.warning(f"月齢解析エラー: {e}")
            return {"use_traditional": True, "phase_text": lunar_phase_text}
    
    def _determine_primary_influence(self, moon_age: float) -> str:
        """月齢から主要な影響を判定"""
        if moon_age <= 3.0:
            return "new_moon"  # 新月期: リセット・回復
        elif moon_age <= 7.0:
            return "waxing_crescent"  # 三日月期: エネルギー上昇開始
        elif moon_age <= 11.0:
            return "waxing_moon"  # 上弦期: 成長・集中力向上
        elif moon_age <= 17.0:
            return "full_moon"  # 満月期: 興奮・睡眠注意
        elif moon_age <= 22.0:
            return "waning_moon"  # 下弦期: 調整・振り返り
        else:
            return "waning_crescent"  # 晦期: 新月準備・デトックス
    
    def _determine_secondary_influence(self, moon_age: float) -> Optional[str]:
        """月齢から副次的な影響を判定（境界期間）"""
        # 各期間の境界±1日は副影響も考慮
        if 2.0 <= moon_age <= 4.0:
            return "new_moon_transition"
        elif 6.0 <= moon_age <= 8.0:
            return "waxing_transition"
        elif 10.0 <= moon_age <= 12.0:
            return "first_quarter_transition"
        elif 16.0 <= moon_age <= 18.0:
            return "full_moon_transition"
        elif 21.0 <= moon_age <= 23.0:
            return "last_quarter_transition"
        elif 26.0 <= moon_age <= 28.0:
            return "new_moon_approach"
        return None
    
    def _calculate_influence_strength(self, moon_age: float) -> str:
        """影響の強度を計算"""
        # 新月・満月に近いほど影響が強い
        new_moon_distance = min(moon_age, 29.5 - moon_age)
        full_moon_distance = abs(moon_age - 14.75)
        
        min_distance = min(new_moon_distance, full_moon_distance)
        
        if min_distance <= 1.0:
            return "strong"  # 強い影響
        elif min_distance <= 2.5:
            return "moderate"  # 中程度の影響
        else:
            return "mild"  # 軽微な影響
    
    def _get_detailed_phase_description(self, moon_age: float) -> str:
        """詳細な月相説明を生成"""
        if moon_age <= 1.0:
            return "新月直後の静寂な時期"
        elif moon_age <= 3.0:
            return "新月期の回復・リセット時期"
        elif moon_age <= 7.0:
            return "三日月期のエネルギー上昇時期"
        elif moon_age <= 11.0:
            return "上弦期の成長・発展時期"
        elif moon_age <= 13.0:
            return "満月に向かう活性化時期"
        elif moon_age <= 16.0:
            return "満月期の高エネルギー時期"
        elif moon_age <= 18.0:
            return "満月後の調整開始時期"
        elif moon_age <= 22.0:
            return "下弦期の整理・振り返り時期"
        elif moon_age <= 26.0:
            return "月末期の準備・デトックス時期"
        else:
            return "新月に向かう準備完了時期"
    
    def generate_llm_lunar_comment(self, lunar_analysis: Dict[str, Any], pressure_context: Dict[str, Any] = None) -> str:
        """LLMを使って月齢に応じた柔軟なコメントを生成"""
        if not self.openai_client or lunar_analysis.get("use_traditional", False):
            # LLMが利用できない場合は従来の方法
            return self._generate_traditional_lunar_comment(lunar_analysis)
        
        try:
            prompt = self._create_lunar_llm_prompt(lunar_analysis, pressure_context)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは受験生・保護者に寄り添う健康サポーターです。月齢の影響について、科学的根拠の限界を明記しつつ、上から目線にならず優しく丁寧な口調でアドバイスしてください。体調を気遣う温かい言葉を使い、「頑張って」のような言葉は避けてください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            st.warning(f"LLM月齢コメント生成エラー: {e}")
            return self._generate_traditional_lunar_comment(lunar_analysis)
    
    def _create_lunar_llm_prompt(self, lunar_analysis: Dict[str, Any], pressure_context: Dict[str, Any] = None) -> str:
        """LLM用の月齢プロンプトを作成"""
        moon_age = lunar_analysis.get("moon_age", 0)
        phase_desc = lunar_analysis.get("phase_description", "")
        primary_influence = lunar_analysis.get("primary_influence", "")
        influence_strength = lunar_analysis.get("influence_strength", "mild")
        
        prompt = f"""受験生・保護者向けの簡潔な月齢アドバイスを生成してください。

【月齢情報】
- 現在の月齢: {moon_age:.1f}日
- 時期: {phase_desc}
- 主要影響: {primary_influence}

【要件】
- 80文字以内の簡潔なアドバイス
- 「参考程度ですが」等で科学的根拠の限界を明記
- 受験生の体調・睡眠への配慮
- 優しく丁寧で寄り添う口調
- 「頑張って」ではなく体調を気遣う温かい言葉

【出力形式】
月齢の特性に基づいた短いアドバイス文を生成してください。"""

        if pressure_context:
            prompt += f"\n\n【気圧情報】\n{pressure_context.get('status', '')}の影響も考慮してください。"
        
        return prompt
    
    def _generate_traditional_lunar_comment(self, lunar_analysis: Dict[str, Any]) -> str:
        """従来の方法で月齢コメントを生成（フォールバック）"""
        phase_text = lunar_analysis.get("phase_text", "")
        
        if "新月" in phase_text:
            return "新月の時期ですね。参考程度ですが、心身のリセットに良いタイミングとされています。十分な休息を取られて、新しいペースで過ごされるのはいかがでしょうか。"
        elif "満月" in phase_text:
            return "満月の時期ですね。一部の研究では睡眠に影響があるとも言われています。就寝環境を整え、ゆったりとお過ごしいただければと思います。"
        else:
            return "月の満ち欠けの時期ですね。参考程度ですが、自然のリズムに合わせて生活を整えることで、穏やかにお過ごしいただけるかもしれません。"
    
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
                lunar_content, practical_advice, rain_advice, perspective,
                weather_info.気圧状況, weather_info.月齢
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
                               perspective: str, pressure_status: str, moon_phase: str) -> str:
        """最終メッセージを構築"""
        
        # 冒頭で気圧配置と月齢を明示
        pressure_moon_intro = self._create_pressure_moon_introduction(pressure_status, moon_phase)
        
        # メッセージ要素を統合
        message_parts = [pressure_moon_intro]
        
        # 体調への影響を説明
        if pressure_content or lunar_content:
            impact_parts = []
            if pressure_content:
                impact_parts.append(pressure_content)
            if lunar_content:
                impact_parts.append(lunar_content)
            message_parts.append(" ".join(impact_parts))
            
        # 具体的なアドバイス
        if practical_advice:
            message_parts.append(practical_advice)
            
        # 雨具のアドバイス
        if rain_advice:
            message_parts.append(rain_advice)
            
        # 温かい労いの言葉で締めくくり
        message_parts.append("受験生の皆様も保護者の方々も、どうぞお体を大切にお過ごしください。")
        
        return "".join(message_parts)
    
    def _create_pressure_moon_introduction(self, pressure_status: str, moon_phase: str) -> str:
        """気圧配置と月齢を明示する冒頭部分を作成"""
        
        # 気圧状況の表現を調整
        if "高気圧" in pressure_status:
            if "気圧の谷" in pressure_status:
                pressure_desc = "高気圧圏内ですが気圧の谷の影響を受け"
            else:
                pressure_desc = "高気圧に覆われ"
        elif "低気圧" in pressure_status:
            pressure_desc = "低気圧の影響を受け"
        elif "気圧の谷" in pressure_status:
            pressure_desc = "気圧の谷の影響で"
        elif "前線" in pressure_status:
            pressure_desc = "前線の影響により"
        else:
            pressure_desc = "穏やかな気圧配置の中"
        
        # 月齢の表現を調整
        if "今日が新月" in moon_phase:
            moon_desc = "今夜は新月の静寂な夜空"
        elif "今日が満月" in moon_phase:
            moon_desc = "今夜は満月の美しい光に包まれた夜空"
        elif "明日が新月" in moon_phase:
            moon_desc = "明日の新月を迎える夜空"
        elif "明日が満月" in moon_phase:
            moon_desc = "明日の満月を前にした夜空"
        elif "新月まであと" in moon_phase:
            moon_desc = f"{moon_phase}の夜空"
        elif "満月まであと" in moon_phase:
            moon_desc = f"{moon_phase}の夜空"
        else:
            moon_desc = "美しい夜空"
        
        return f"今日は{pressure_desc}、{moon_desc}となります。"
    
    def _generate_fallback_message(self, weather_info: WeatherInfo) -> str:
        """フォールバックメッセージを生成"""
        return f"本日は{weather_info.快適具合}一日となる予想です。{weather_info.月齢}の時期で{weather_info.気圧状況}の影響もございますので、体調管理にお気をつけください。"
    
    def generate_student_focused_message(self, weather_info: WeatherInfo, moon_age: Optional[float] = None) -> str:
        """受験生・保護者向けの配慮深いメッセージを生成（LLM月齢対応）"""
        try:
            # 気圧アドバイスを取得
            pressure_advice = self.get_specialized_pressure_advice(weather_info.気圧状況)
            
            # 月齢の詳細解析を実行
            lunar_analysis = self.get_precise_lunar_data(weather_info.月齢, moon_age)
            
            # LLMを使った柔軟な月齢コメント生成
            if not lunar_analysis.get("use_traditional", False) and self.openai_client:
                lunar_comment = self.generate_llm_lunar_comment(
                    lunar_analysis, 
                    {"status": weather_info.気圧状況}
                )
                # LLMコメントと気圧アドバイスを統合
                return self._integrate_llm_student_advice(pressure_advice, lunar_comment, lunar_analysis)
            else:
                # 従来の方法
                lunar_advice = self.get_specialized_lunar_advice(weather_info.月齢)
                return self._integrate_student_advice(pressure_advice, lunar_advice)
            
        except Exception as e:
            st.warning(f"受験生向けメッセージ生成エラー: {e}")
            return self._generate_fallback_message(weather_info)
    
    def _integrate_llm_student_advice(self, pressure_advice: Dict[str, Any], lunar_comment: str, lunar_analysis: Dict[str, Any]) -> str:
        """気圧アドバイスとLLM生成月齢コメントを統合（コンパクト版）"""
        try:
            # コンパクトな統合メッセージを生成
            return self._generate_compact_integrated_message(pressure_advice, lunar_comment, lunar_analysis)
            
        except Exception as e:
            st.warning(f"統合メッセージ生成エラー: {e}")
            return self._generate_simple_fallback_message(pressure_advice, lunar_comment)
    
    def _generate_compact_integrated_message(self, pressure_advice: Dict[str, Any], lunar_comment: str, lunar_analysis: Dict[str, Any]) -> str:
        """コンパクトで一貫性のある統合メッセージを生成"""
        if not self.openai_client:
            return self._generate_simple_fallback_message(pressure_advice, lunar_comment)
        
        try:
            # 気圧と月齢の情報を統合したプロンプトを作成
            integration_prompt = self._create_integration_prompt(pressure_advice, lunar_comment, lunar_analysis)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは受験生・保護者に寄り添う健康サポーターです。上から目線にならず、優しく丁寧な口調で、気圧と月齢の影響を統合したアドバイスを生成してください。「頑張って」のような励ましではなく、体調を気遣う温かい言葉を使ってください。"},
                    {"role": "user", "content": integration_prompt}
                ],
                max_tokens=200,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            st.warning(f"LLM統合メッセージ生成エラー: {e}")
            return self._generate_simple_fallback_message(pressure_advice, lunar_comment)
    
    def _create_integration_prompt(self, pressure_advice: Dict[str, Any], lunar_comment: str, lunar_analysis: Dict[str, Any]) -> str:
        """統合メッセージ用のプロンプトを作成"""
        pressure_status = pressure_advice.get("tone_elements", {}).get("caring_expression", "")
        pressure_impact = pressure_advice.get("student_advice", {}).get("immediate_actions", "")
        pressure_study = pressure_advice.get("student_advice", {}).get("study_adjustments", "")
        
        moon_age = lunar_analysis.get("moon_age", 0)
        phase_desc = lunar_analysis.get("phase_description", "")
        
        prompt = f"""気圧と月齢の情報を統合して、受験生・保護者向けのコンパクトなアドバイスを生成してください。

【気圧情報】
- 状況: {pressure_status}
- 体調への影響: {pressure_impact}
- 学習への影響: {pressure_study}

【月齢情報】
- 月齢: {moon_age:.1f}日
- 時期: {phase_desc}
- LLMコメント: {lunar_comment}

【要件】
- 120文字以内のコンパクトなメッセージ
- 重複する内容は統合する
- 受験生と保護者両方への配慮
- 優しく丁寧で寄り添う口調
- 「頑張って」ではなく体調を気遣う温かい言葉
- 気圧と月齢の影響を自然に組み合わせる

【出力形式】
統合された一つの自然なアドバイス文を生成してください。"""
        
        return prompt
    
    def _generate_simple_fallback_message(self, pressure_advice: Dict[str, Any], lunar_comment: str) -> str:
        """シンプルなフォールバックメッセージを生成"""
        pressure_tone = pressure_advice.get("tone_elements", {}).get("caring_expression", "")
        
        # 基本的な気圧メッセージ
        if pressure_tone:
            base_message = f"{pressure_tone}。"
        else:
            base_message = "今日も受験勉強お疲れ様です。"
        
        # 月齢コメントがあれば追加（短縮）
        if lunar_comment and len(lunar_comment) < 100:
            base_message += lunar_comment
        
        # 簡潔な締めくくり
        base_message += "どうぞお体を大切にお過ごしください。"
        
        return base_message
    
    def _get_school_context(self) -> str:
        """日本大学第一中学・高等学校の基本情報を取得"""
        return """
あなたは日本大学第一中学・高等学校のメルマガ担当です。以下の学校情報を活用してください：

【学校概要】
- 名称: 日本大学第一中学・高等学校（日大一中・日大一高）
- 所在地: 東京都墨田区横網（両国地区）
- アクセス: 総武線・大江戸線駅近、A1出口からすぐの好立地
- 生徒数: 中学605名（各学年200名）、高校1042名（1学年350名）
- 共学校: 男女比 男子6：女子4（最近は女子比率上昇傾向）

【通学圏・特色】
- 中学: 東京76.5%、千葉17%（通学時間45-50分が8割）
- 高校: 東京6割、千葉3割超（通学時間60分が主要層）
- 下町エリア（江東・江戸川・墨田・葛飾・台東・荒川）から多数通学
- 駐輪場なしのため電車通学中心

【教育システム】
- 6年一貫教育（中学→高校進学は成績基準あり、約90-95%が内部進学）
- 基礎期（中1-2）: 生活習慣・学習習慣の定着を重視
- 定着期（中3-高1）: 進路探求と多様な刺激による視野拡大
- 入試期（高2-3）: 日大進学コースと難関私大コースに分化

【進路実績】
- 日本大学進学率: 70%超（付属校26校中でも日大志向が特に強い）
- 日大内第一希望学部合格率: 80%超
- 他大学進学: 上智・東京理科・学習院・法政等（指定校推薦あり）
- 基礎学力到達度テスト: 学校授業+無料講習で塾なし対応可能

【部活動・学校生活】
- 部活動参加率: 中学66.6%、高校61.1%、全体63%
- 校友会主任の理念: 「人生に必要なことを学ぶ場」
- 答えが見えない中でも前向きに取り組む力を育成
- 朝8:15-夕方18:00の充実した学校生活

【入試情報】
- 中学入試: 4回実施（4科2回・2科2回、計200名募集）
- 高校入試: 単願推薦75名・一般入試75名（併願優遇なし）
- 推薦基準: 5教科20以上、各学年欠席10日以内、通知表に1なし等

【学校の雰囲気・特徴】
- 日大進学を目標とした確実な学習サポート体制
- 部活動と勉強の両立を重視
- 面倒見の良い指導（提出物管理、小テスト再試験等）
- 下町の温かい雰囲気と都心アクセスの良さを併せ持つ
"""
    
    def _get_school_intro_themes(self) -> List[str]:
        """学校紹介のテーマリストを取得"""
        return [
            "進学実績_日大進学率70%超の安心感",
            "立地環境_両国駅近の好アクセス",
            "部活動_人生に必要なことを学ぶ場",
            "教育システム_6年一貫の手厚いサポート",
            "学習環境_塾なし対応の無料講習",
            "面倒見_提出物管理から進路相談まで",
            "進路選択_日大進学と難関私大の両立",
            "学校生活_朝8時15分から夕方6時の充実",
            "入試制度_複数回受験チャンスあり",
            "通学環境_下町エリアからの通いやすさ",
            "校風_温かい雰囲気と都心利便性",
            "サポート体制_基礎から応用まで段階的指導"
        ]
    
    def _select_school_intro_theme(self, weather_context: str, lunar_context: str) -> str:
        """天気・月齢・履歴を考慮して学校紹介テーマを選択"""
        available_themes = self._get_school_intro_themes()
        
        # 過去1週間で使用したテーマを除外
        recent_themes = [item.split('_')[0] for item in self.school_intro_history[-5:]]
        unused_themes = [theme for theme in available_themes 
                        if theme.split('_')[0] not in recent_themes]
        
        # 未使用テーマがない場合は全テーマから選択
        if not unused_themes:
            unused_themes = available_themes
        
        # 天気・月齢に応じた重み付け選択
        if "雨" in weather_context or "低気圧" in weather_context:
            # 屋内環境重視
            preferred = [t for t in unused_themes if any(keyword in t for keyword in 
                        ["学習環境", "面倒見", "サポート体制", "教育システム"])]
        elif "高気圧" in weather_context or "晴" in weather_context:
            # アクティブな要素重視
            preferred = [t for t in unused_themes if any(keyword in t for keyword in 
                        ["部活動", "立地環境", "学校生活", "校風"])]
        else:
            preferred = unused_themes
        
        # 選択肢がない場合は全未使用テーマから
        if not preferred:
            preferred = unused_themes
        
        selected_theme = random.choice(preferred)
        
        # 履歴に追加
        self.school_intro_history.append(selected_theme)
        if len(self.school_intro_history) > self.max_history_length:
            self.school_intro_history.pop(0)
        
        return selected_theme
    
    def _integrate_student_advice(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """気圧と月齢のアドバイスを統合して受験生向けメッセージを生成"""
        message_parts = []
        
        # 1. 冒頭：優しい気遣いの表現
        intro = self._create_caring_introduction(pressure_advice, lunar_advice)
        message_parts.append(intro)
        
        # 2. 具体的な体調への影響と対策
        health_advice = self._create_health_guidance(pressure_advice, lunar_advice)
        if health_advice:
            message_parts.append(health_advice)
        
        # 3. 学習面でのアドバイス
        study_advice = self._create_study_guidance(pressure_advice, lunar_advice)
        if study_advice:
            message_parts.append(study_advice)
        
        # 4. 保護者向けのサポート提案
        parent_advice = self._create_parent_guidance(pressure_advice, lunar_advice)
        if parent_advice:
            message_parts.append(parent_advice)
        
        # 5. 締めくくり：励ましと安心の言葉
        conclusion = self._create_encouraging_conclusion(pressure_advice, lunar_advice)
        message_parts.append(conclusion)
        
        return "".join(message_parts)
    
    def _create_caring_introduction(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """優しい気遣いの冒頭文を作成"""
        pressure_tone = pressure_advice.get("tone_elements", {}).get("caring_expression", "")
        lunar_tone = lunar_advice.get("tone_elements", {}).get("caring_expression", "")
        
        if pressure_tone and lunar_tone:
            return f"{pressure_tone}。また、{lunar_tone}。"
        elif pressure_tone:
            return f"{pressure_tone}。"
        elif lunar_tone:
            return f"{lunar_tone}。"
        else:
            return "受験生の皆様、保護者の皆様、いつもお疲れ様です。"
    
    def _create_health_guidance(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """体調管理に関するアドバイスを作成"""
        advice_parts = []
        
        # 気圧による影響と対策
        pressure_student = pressure_advice.get("student_advice", {})
        if pressure_student.get("immediate_actions"):
            advice_parts.append(f"体調面では、{pressure_student['immediate_actions']}ことが大切です。")
        
        # 月齢による影響と対策（科学的根拠の限界を明記）
        lunar_student = lunar_advice.get("student_advice", {})
        if lunar_student.get("self_care"):
            advice_parts.append(f"また、参考程度ですが、{lunar_student['self_care']}と良いとされています。")
        
        return "".join(advice_parts)
    
    def _create_study_guidance(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """学習面でのアドバイスを作成"""
        advice_parts = []
        
        # 気圧による学習への影響
        pressure_study = pressure_advice.get("student_advice", {}).get("study_adjustments", "")
        if pressure_study:
            advice_parts.append(f"勉強面では、{pressure_study}ことをおすすめします。")
        
        # 月齢による学習アプローチ
        lunar_study = lunar_advice.get("student_advice", {}).get("study_adjustments", "")
        if lunar_study:
            advice_parts.append(f"この時期は{lunar_study}のも良いでしょう。")
        
        return "".join(advice_parts)
    
    def _create_parent_guidance(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """保護者向けのアドバイスを作成"""
        advice_parts = []
        
        # 気圧に関する保護者の注意点
        pressure_parent = pressure_advice.get("parent_guidance", {})
        if pressure_parent.get("observation_points"):
            advice_parts.append(f"保護者の方は、{pressure_parent['observation_points']}などにご注意ください。")
        
        if pressure_parent.get("support_methods"):
            advice_parts.append(f"{pressure_parent['support_methods']}といったサポートも効果的です。")
        
        return "".join(advice_parts)
    
    def _create_encouraging_conclusion(self, pressure_advice: Dict[str, Any], lunar_advice: Dict[str, Any]) -> str:
        """励ましと安心の締めくくりを作成"""
        pressure_encouragement = pressure_advice.get("tone_elements", {}).get("encouragement", "")
        lunar_encouragement = lunar_advice.get("tone_elements", {}).get("encouragement", "")
        
        conclusion_options = [
            "受験は長い道のりですが、体調を第一に、一歩ずつ着実に進んでいきましょう。",
            "無理をせず、お体を大切にしながら目標に向かって頑張ってください。",
            "皆様が健康で充実した日々を送られることを心より願っております。"
        ]
        
        if pressure_encouragement:
            return f"{pressure_encouragement}。{random.choice(conclusion_options)}"
        elif lunar_encouragement:
            return f"{lunar_encouragement}。{random.choice(conclusion_options)}"
        else:
            return random.choice(conclusion_options)
    


