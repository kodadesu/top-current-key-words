import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# アプリのタイトルと基本設定（ブラウザのタブ名のみ残します）
st.set_page_config(page_title="社会の関心ワード ダッシュボード", layout="centered")

# 各項目の表示件数は10件に固定
FIXED_ITEMS = 10

# =================================================================
# 1. Wikipedia（閲覧数急上昇・人名フィルターなし）
# =================================================================
st.header("📝 Wikipedia 閲覧数ランキング")

yesterday = datetime.now() - timedelta(days=1)
date_str = yesterday.strftime("%Y/%m/%d")
st.caption(f"昨日（{yesterday.strftime('%m月%d日')}）に日本中で最も読まれた記事（人名を含む）")

try:
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/ja.wikipedia/all-access/{date_str}"
    req = urllib.request.Request(url, headers={'User-Agent': 'TrendChecker/1.0 (contact: test@example.com)'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode('utf-8'))
    articles = data["items"][0]["articles"]
    
    wiki_data = []
    count = 1
    for item in articles:
        if count > FIXED_ITEMS:
            break
            
        title = item["article"].replace("_", " ")
        views = item["views"]
        
        if title in ["メインページ", "特別:検索", "特別:最近の更新"]:
            continue
        
        wiki_data.append({"順位": count, "キーワード（人名含む）": title, "アクセス数": f"{views:,} 回"})
        count += 1
        
    df_wiki = pd.DataFrame(wiki_data).set_index("順位")
    st.table(df_wiki)
        
except Exception as e:
    st.error(f"Wikipediaデータの取得に失敗しました: {e}")

# =================================================================
# 2. Yahoo!ニュース（主要・経済・国内）
# =================================================================
st.divider()
st.header("📰 Yahoo!ニューストピックス")

# カテゴリ選択用のセレクトボックス
genre = st.selectbox(
    "ニュースカテゴリを選択してください",
    ["主要トピックス", "国内ニュース", "経済・ビジネス", "IT・科学", "エンタメ", "ライフ"]
)

urls = {
    "主要トピックス": "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
    "国内ニュース": "https://news.yahoo.co.jp/rss/categories/domestic.xml",
    "経済・ビジネス": "https://news.yahoo.co.jp/rss/categories/business.xml",
    "IT・科学": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "エンタメ": "https://news.yahoo.co.jp/rss/categories/entertainment.xml",
    "ライフ": "https://news.yahoo.co.jp/rss/categories/life.xml"
}

try:
    url = urls[genre]
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    xml_data = response.read()
    root = ET.fromstring(xml_data)
    
    yahoo_data = []
    for count, item in enumerate(root.findall(".//item")[:FIXED_ITEMS], 1):
        title = item.find("title").text
        yahoo_data.append({"順位": count, "ニュースタイトル": title})
        
    df_yahoo = pd.DataFrame(yahoo_data).set_index("順位")
    st.table(df_yahoo)
    
except Exception as e:
    st.error(f"Yahoo!ニュースの取得に失敗しました: {e}")

# =================================================================
# 3. Googleトレンド（急上昇ワード）
# =================================================================
st.divider()
st.header("🔥 Google急上昇ワード")
st.caption("リアルタイムで検索急増中のキーワード（スポーツ紙ソース除外）")

try:
    url = "https://trends.google.co.jp/trending/rss?geo=JP"
    response = urllib.request.urlopen(url)
    xml_data = response.read()
    root = ET.fromstring(xml_data)
    ns = {"ht": "https://trends.google.com/trending/rss"}

    google_data = []
    count = 1
    for item in root.findall(".//item"):
        if count > FIXED_ITEMS:
            break
            
        title = item.find("title").text
        news_item = item.find(".//ht:news_item_title", namespaces=ns)
        news_source = item.find(".//ht:news_item_source", namespaces=ns)
        
        # スポーツ系ソースの除外フィルター
        if news_item is not None and news_source is not None:
            source_name = news_source.text
            if "スポーツ" in source_name or "スポ" in source_name:
                continue
        
        news_title = news_item.text if news_item is not None else "（関連ニュースなし）"
        
        google_data.append({"順位": count, "キーワード": title, "関連ニュース": news_title})
        count += 1
    
    df_google = pd.DataFrame(google_data).set_index("順位")
    st.table(df_google)
        
except Exception as e:
    st.error(f"Googleトレンドの取得に失敗しました: {e}")
