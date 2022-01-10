import requests
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS
from requests.api import head

class RSSReader:

    @classmethod
    def seekingalpha(cls, ticker, timestamps=False) -> list:
        url = f"https://seekingalpha.com/api/sa/combined/{ticker.upper()}.xml"
        
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
            dct["type"] = "news" if "https://seekingalpha.com/news/" in dct["url"] else "article" if "https://seekingalpha.com/article/" in dct["url"] else "unclassified"
            data.append(dct)
            
        return data

    @classmethod
    def nasdaq(cls):
        pass

    @classmethod
    def wsj(cls):
        pass

    @classmethod
    def cnbc(cls):
        pass