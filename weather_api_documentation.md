# お天気APIで取得できる情報の一覧

このプログラムでは、2つの天気予報APIを組み合わせて包括的な気象情報を取得しています。

## 1. 気象庁互換API (weather.tsukumijima.net)

### 基本情報
- **URL**: `https://weather.tsukumijima.net/api/forecast?city=130010`
- **地域**: 東京地方（墨田区横網）
- **データ形式**: JSON
- **用途**: 基本的な天気情報（気温、天気概況、降水確率など）

### 取得可能なデータ項目

#### 基本情報
- `publicTime`: 発表時刻（ISO形式）
- `publicTimeFormatted`: 発表時刻（フォーマット済み）
- `publishingOffice`: 発表官署
- `title`: タイトル

#### 地域情報
- `location.area`: 地域名
- `location.prefecture`: 都道府県名
- `location.district`: 地区名
- `location.city`: 市区町村名

#### 天気予報データ（forecasts配列）
- `date`: 予報日（YYYY-MM-DD形式）
- `dateLabel`: 日付ラベル（今日/明日/明後日）
- `telop`: 天気概況（テキスト）
- `detail.weather`: 詳細天気
- `detail.wind`: 風の情報
- `detail.wave`: 波の情報

#### 気温データ
- `temperature.min.celsius`: 最低気温（℃）
- `temperature.max.celsius`: 最高気温（℃）

#### 降水確率データ
- `chanceOfRain.T00_06`: 降水確率 0-6時（%）
- `chanceOfRain.T06_12`: 降水確率 6-12時（%）
- `chanceOfRain.T12_18`: 降水確率 12-18時（%）
- `chanceOfRain.T18_24`: 降水確率 18-24時（%）

#### 天気アイコン
- `image.title`: 天気アイコンのタイトル
- `image.url`: 天気アイコンのURL
- `image.width`: アイコン幅
- `image.height`: アイコン高さ

#### 著作権・利用規約情報
- `copyright.title`: 著作権表示タイトル
- `copyright.link`: 著作権情報URL
- `copyright.image.title`: 提供元画像タイトル
- `copyright.image.link`: 提供元画像URL
- `copyright.image.url`: 提供元画像ファイルURL
- `copyright.image.width`: 画像幅
- `copyright.image.height`: 画像高さ

## 2. Open-Meteo API

### 基本情報
- **URL**: `https://api.open-meteo.com/v1/forecast`
- **座標**: 緯度35.70, 経度139.798（墨田区横網）
- **用途**: 湿度データの補完
- **データ形式**: JSON
- **予報日数**: 3日分

### パラメータ
```
latitude=35.70
longitude=139.798
daily=relative_humidity_2m_max,relative_humidity_2m_min
timezone=Asia%2FTokyo
forecast_days=3
```

### 取得可能なデータ項目

#### 基本情報
- `latitude`: 緯度
- `longitude`: 経度
- `generationtime_ms`: 生成時間（ミリ秒）
- `utc_offset_seconds`: UTCオフセット（秒）
- `timezone`: タイムゾーン
- `timezone_abbreviation`: タイムゾーン略称
- `elevation`: 標高（m）

#### 湿度データ（daily配列）
- `daily.time`: 日付配列（YYYY-MM-DD形式）
- `daily.relative_humidity_2m_max`: 最大相対湿度（%）
- `daily.relative_humidity_2m_min`: 最小相対湿度（%）

#### 単位情報（daily_units）
- `daily_units.time`: 時間の単位
- `daily_units.relative_humidity_2m_max`: 最大湿度の単位
- `daily_units.relative_humidity_2m_min`: 最小湿度の単位

## 3. データ統合処理

このプログラムでは、以下の3ステップでデータを統合しています：

### Step 1: 気象庁互換APIで基本天気データ取得
```python
weather_data = self.weather_service.load_weather_data(target_date)
```
- 天気概況、気温、降水確率、風などの基本情報
- 気象庁の公式データに基づく信頼性の高い情報

### Step 2: Open-Meteo APIで湿度データを補完
```python
humidity_data = self.weather_service.get_humidity_data(target_date)
```
- 相対湿度の最大値・最小値
- 気象庁互換APIでは提供されない湿度情報を補完

### Step 3: 両方のデータを統合
```python
combined_weather_data = self.weather_service.merge_weather_data(weather_data, humidity_data)
```
- `weather_service.py` の `merge_weather_data()` メソッドで統合
- 基本天気データに湿度情報を追加
- メルマガ生成時に包括的な天気情報として活用

## 4. プログラムでの使用例

### 湿度データの取得と処理
```python
def get_humidity_for_date(self, target_date: date) -> str:
    """指定日の湿度データを取得"""
    data = self.get_humidity_data(target_date)
    
    if "daily" in data and "time" in data["daily"]:
        date_str = target_date.strftime("%Y-%m-%d")
        if date_str in data["daily"]["time"]:
            index = data["daily"]["time"].index(date_str)
            h_max = data["daily"]["relative_humidity_2m_max"][index]
            h_min = data["daily"]["relative_humidity_2m_min"][index]
            
            if h_max is not None and h_min is not None:
                return f"{h_min}-{h_max}%"
    
    return "データなし"
```

### データの統合処理
```python
def merge_weather_data(self, weather_data: dict, humidity_data: dict) -> dict:
    """天気データと湿度データを統合"""
    if not weather_data:
        return None
    
    # 基本の天気データをコピー
    merged_data = weather_data.copy()
    
    # 湿度データを追加
    if humidity_data and 'daily' in humidity_data:
        merged_data['humidity_data'] = humidity_data['daily']
    
    return merged_data
```

## 5. 利用上の注意点

### 気象庁互換API
- **利用制限**: 特になし（個人利用範囲）
- **更新頻度**: 気象庁の発表に準拠（通常1日3-4回）
- **データの正確性**: 気象庁データベースを使用
- **レスポンス形式**: JSON
- **信頼性**: 高い（公式データ）

### Open-Meteo API
- **利用制限**: 1日10,000リクエスト（無料枠）
- **更新頻度**: 1時間毎
- **データソース**: 複数の気象モデル（GFS、ICON等）
- **レスポンス形式**: JSON
- **信頼性**: 中程度（予測モデルベース）

### 法的コンプライアンス
- ✅ **公式APIを使用**（Webスクレイピングなし）
- ✅ **利用規約に準拠**
- ✅ **著作権情報を適切に表示**
- ✅ **商用利用における制限を遵守**

## 6. エラーハンドリング

### API接続エラー
- ネットワークエラー時は "データなし" を表示
- API制限到達時は翌日データで代替
- タイムアウト時は再試行機能を実装

### データ欠損対応
- 気温データが無い場合: "気温情報なし"
- 湿度データが無い場合: "湿度情報なし"
- 推定値は使用せず、実データのみ使用

## 7. 実装ファイル

- **`weather_service.py`**: 両APIの呼び出しとデータ統合
- **`newsletter_generator.py`**: 3ステップ統合処理の実行
- **`config.py`**: API設定とデータ構造定義
- **`utils.py`**: 日付処理とユーティリティ関数