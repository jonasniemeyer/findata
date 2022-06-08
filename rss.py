import requests
import pandas as pd
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS

class RSSReader:

    @classmethod
    def seekingalpha(cls, ticker, timestamps=False) -> list:
        url = f"https://seekingalpha.com/api/sa/combined/{ticker}.xml"
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")
        
        data = []
        for tag in tags:
            dct = {}
            dct["header"] = tag.find("title").text
            dct["url"] = tag.find("guid").text.replace("Article:", "article/").replace("MarketCurrent:", "news/")
            date =  tag.find("pubdate").text
            date = int(pd.to_datetime(date).timestamp())
            if not timestamps:
                date = pd.to_datetime(date, unit="s").isoformat()
            dct["date"] = date
            dct["author"] = tag.find("sa:author_name").text
            dct["type"] = "News" if "https://seekingalpha.com/news/" in dct["url"] else "Article" if "https://seekingalpha.com/article/" in dct["url"] else "Unclassified"
            data.append(dct)
            
        return data

    @classmethod
    def nasdaq(cls, ticker, timestamps=False) -> list:
        url = f"https://www.nasdaq.com/feed/rssoutbound?symbol={ticker}"
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")
        
        data = []
        for tag in tags:
            dct = {}
            dct["header"] = tag.find("title").text
            dct["url"] = tag.find("guid").text
            date =  tag.find("pubdate").text
            date = int(pd.to_datetime(date).timestamp())
            if not timestamps:
                date = pd.to_datetime(date, unit="s").isoformat()
            dct["date"] = date
            dct["category"] = tag.find("category").text
            data.append(dct)
            
        return data

    @classmethod
    def wsj(cls, source, timestamps=False) -> list:
        url = "https://feeds.a.dj.com/rss/{}.xml"
        if source not in ("opinion", "world", "us business", "markets", "technology", "lifestyle"):
            raise ValueError("source has to be in ('opinion', 'world', 'us business', 'markets', 'technology', 'lifestyle')")
        if source == "opinion":
            url = url.format("RSSOpinion")
        elif source == "world":
            url = url.format("RSSWorldNews")
        elif source == "us business":
            url = url.format("WSJcomUSBusiness")
        elif source == "markets":
            url = url.format("RSSMarketsMain")
        elif source == "technology":
            url = url.format("RSSWSJD")
        elif source == "lifestyle":        
            url = url.format("RSSLifestyle")
        
        response = requests.get(url=url, headers=HEADERS).text
        soup = BeautifulSoup(response, "lxml")
        tags = soup.find_all("item")

        data = []
        for tag in tags:
            dct = {}
            dct["header"] = tag.find("title").text
            dct["url"] = f"https://www.wsj.com/articles/{tag.find('guid').text}"
            date =  tag.find("pubdate").text
            date = int(pd.to_datetime(date).timestamp())
            if not timestamps:
                date = pd.to_datetime(date, unit="s").isoformat()
            dct["date"] = date
            data.append(dct)
            
        return data