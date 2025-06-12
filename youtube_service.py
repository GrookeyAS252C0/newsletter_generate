"""
YouTube API サービス - 簡易版（字幕機能削除済み）
"""

import time
from datetime import date
from typing import List, Optional

try:
    import streamlit as st
except ImportError:
    class DummySt:
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    st = DummySt()

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    st.warning("google-api-python-clientがインストールされていません: pip install google-api-python-client")
    # YouTube機能は無効化されますが、他の機能は動作します
    build = None
    HttpError = Exception

from config import YouTubeVideo
from utils import DateUtils


class YouTubeService:
    """YouTube API関連の処理を担当（字幕機能削除済み）"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if build:
            try:
                self.youtube = build('youtube', 'v3', developerKey=api_key)
            except Exception as e:
                st.error(f"YouTube APIの初期化に失敗: {e}")
                self.youtube = None
        else:
            self.youtube = None
    
    def get_channel_id(self, channel_handle: str) -> Optional[str]:
        """チャンネルハンドルからチャンネルIDを取得"""
        if not self.youtube:
            return None
            
        search_queries = [
            f"@{channel_handle}",
            channel_handle,
            "日本大学第一中学",
            "日大一",
            "日本大学第一中学・高等学校"
        ]
        
        for query in search_queries:
            try:
                search_response = self.youtube.search().list(
                    q=query,
                    type='channel',
                    part='id,snippet',
                    maxResults=10
                ).execute()
                
                for item in search_response['items']:
                    channel_title = item['snippet']['title']
                    if any(keyword in channel_title for keyword in ["日本大学第一", "日大一", "nichidaiichi"]):
                        channel_id = item['id']['channelId']
                        st.info(f"✅ チャンネルを特定: {channel_title} (ID: {channel_id[:10]}...)")
                        return channel_id
                
                time.sleep(0.1)
                
            except HttpError as e:
                st.warning(f"検索クエリ '{query}' でエラー: {e}")
                continue
            except Exception as e:
                st.error(f"チャンネル検索中にエラー: {e}")
                continue
        
        st.warning("チャンネルIDの取得に失敗しました")
        return None
    
    def search_videos_by_date(self, target_date: date, channel_id: Optional[str] = None) -> List[YouTubeVideo]:
        """指定日に完全一致する動画を検索（タイトルに日付が含まれるもののみ）"""
        if not self.youtube:
            st.warning("YouTube APIが利用できません")
            return []
            
        try:
            if not channel_id:
                channel_id = self.get_channel_id("nichidaiichi")
            
            # 完全一致検索のため、主要な日付形式を使用（YYYY年MM月DD日, YYYY/MM/DD, YYYY-MM-DD, YYYY\MM/DD）
            date_queries = DateUtils.get_date_formats(target_date)[:7]  # 最初の7つにはYYYY\MM/DDパターンも含まれる
            found_videos = []
            
            st.info(f"🎯 {target_date.strftime('%Y年%m月%d日')}に完全一致する動画を検索中...")
            
            for query in date_queries:
                try:
                    videos = self._search_videos_with_query(query, channel_id, target_date)
                    found_videos.extend(videos)
                    time.sleep(0.2)
                    
                except HttpError as e:
                    if e.resp.status == 403:
                        st.error("YouTube API クォータに達しました")
                        break
                    else:
                        st.warning(f"検索エラー (クエリ: {query}): {e}")
                        continue
                except Exception as e:
                    st.warning(f"動画検索中にエラー (クエリ: {query}): {e}")
                    continue
            
            return self._remove_duplicates(found_videos)
            
        except Exception as e:
            st.error(f"YouTube動画検索エラー: {e}")
            return []
    
    def _search_videos_with_query(self, query: str, channel_id: Optional[str], 
                                 target_date: date) -> List[YouTubeVideo]:
        """特定のクエリで動画を検索"""
        if channel_id:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                q=query,
                type='video',
                part='id,snippet',
                maxResults=10,
                order='date'
            ).execute()
        else:
            search_response = self.youtube.search().list(
                q=f"日本大学第一中学・高等学校 {query}",
                type='video',
                part='id,snippet',
                maxResults=5,
                order='relevance'
            ).execute()
        
        st.info(f"🔍 検索: '{query}' で {len(search_response['items'])} 件見つかりました")
        
        videos = []
        date_queries = DateUtils.get_date_formats(target_date)
        
        for item in search_response['items']:
            video_title = item['snippet']['title']
            
            # タイトルに日付が含まれているかチェック（完全一致のみ）
            # メインの日付形式をチェック（YYYY年MM月DD日, YYYY/MM/DD, YYYY-MM-DD, YYYY\MM/DD等）
            exact_date_formats = date_queries[:7] if len(date_queries) >= 7 else date_queries
            
            if any(date_str in video_title for date_str in exact_date_formats):
                videos.append(YouTubeVideo(
                    title=video_title,
                    url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    published_at=item['snippet']['publishedAt'],
                    thumbnail=item['snippet']['thumbnails']['default']['url'],
                    channel_title=item['snippet']['channelTitle'],
                    matched_query=query
                ))
                st.success(f"📹 マッチした動画: {video_title[:50]}...")
        
        return videos
    
    def _remove_duplicates(self, videos: List[YouTubeVideo]) -> List[YouTubeVideo]:
        """重複動画を除去"""
        unique_videos = []
        seen_urls = set()
        
        for video in videos:
            if video.url not in seen_urls:
                unique_videos.append(video)
                seen_urls.add(video.url)
        
        if unique_videos:
            st.success(f"🎯 最終結果: {len(unique_videos)} 件のユニークな動画が見つかりました")
        else:
            st.info("🔍 関連する動画は見つかりませんでした")
        
        return unique_videos