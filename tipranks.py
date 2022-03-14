import pandas as pd
import requests
from finance_data.utils import TIPRANKS_HEADERS

class TipranksReader:
    _base_url = "https://www.tipranks.com/api/stocks/"
    
    def __init__(self, ticker) -> None:
        self.ticker = ticker

    @classmethod
    def trending_stocks(cls, timestamps=False):
        data = requests.get(
            url = f"{cls._base_url}gettrendingstocks/",
            headers = TIPRANKS_HEADERS,
            params = {
                "daysago": 30,
                "which": "most"
            }
        ).json()
        
        data = [
            {
                "ticker": item["ticker"],
                "name": item["companyName"],
                "popularity": item["popularity"],
                "sentiment": item["sentiment"],
                "consensus_score": round(item["consensusScore"], 6),
                "sector": item["sector"],
                "market_cap": item["marketCap"],
                "buy": item["buy"],
                "hold": item["hold"],
                "sell": item["sell"],
                "consensus_rating": item["rating"],
                "price_target": item["priceTarget"],
                "latest_rating": (
                    int(pd.to_datetime(item["lastRatingDate"]).date().timestamps()) if timestamps
                    else pd.to_datetime(item["lastRatingDate"]).date().isoformat()
                )
            }
            for item in data
        ]
        
        return data
    
    @property
    def isin(self):
        return self._get_ratings_data()["isin"]
    
    def news_sentiment(self, timestamps=False):
        data = requests.get(
            url = f"{self._base_url}getNewsSentiments/",
            headers = TIPRANKS_HEADERS,
            params = {"ticker": self.ticker}
        ).json()
        
        data = {
            "articles_last_week": data["buzz"]["articlesInLastWeek"],
            "average_weekly_articles": data["buzz"]["weeklyAverage"],
            "positive_percent": data["sentiment"]["bullishPercent"],
            "negative_percent": data["sentiment"]["bearishPercent"],
            "sector_sentiment": [
                {
                    "ticker": item["ticker"],
                    "name": item["companyName"],
                    "positive_percent": item["bullishPercent"],
                    "negative_percent": item["bearishPercent"]
                } 
                for item in data["sector"]
            ],
            "sector_average_sentiment": data["sectorAverageBullishPercent"],
            "news_score": data["score"],
            "articles": [
                {
                    "week": (
                        int(pd.to_datetime(item["weekStart"]).date().timestamps()) if timestamps
                        else pd.to_datetime(item["weekStart"]).date().isoformat()
                    ),
                    "buy": item["buy"],
                    "neutral": item["neutral"],
                    "sell": item["sell"],
                    "total": item["all"]
                }
                for item in data["counts"]
            ],
            "sector_average_news_score": data["sectorAverageNewsScore"]

        }
        
        return data

    def recommendation_trend_breakup(self, timestamps=False, sorted_by="stars"):
        data_raw = self._get_ratings_data()["consensuses"]
        data = {}
        if sorted_by == "stars":
            for item in data_raw:
                stars = item["mStars"]
                date = pd.to_datetime(item["d"]).date()
                date = date.timestamp() if timestamps else date.isoformat()
                
                data[stars] = data.get(stars, {})
                data[stars][date] = data.get(date, {})
                data[stars][date]["consensus_rating"] = item["rating"]
                data[stars][date]["buy"] = item["nB"]
                data[stars][date]["hold"] = item["nH"]
                data[stars][date]["sell"] = item["nS"]
                data[stars][date]["average"] = (item["nB"]*5+item["nH"]*3+item["nS"]) / (item["nB"]+item["nH"]+item["nS"])
        elif sorted_by == "date":
            for item in data_raw:
                stars = item["mStars"]
                date = pd.to_datetime(item["d"]).date()
                date = date.timestamp() if timestamps else date.isoformat()
                
                data[date] = data.get(date, {})
                data[date][stars] = data.get(stars, {})
                data[date][stars]["consensus_rating"] = item["rating"]
                data[date][stars]["buy"] = item["nB"]
                data[date][stars]["hold"] = item["nH"]
                data[date][stars]["sell"] = item["nS"]
                data[date][stars]["average"] = (item["nB"]*5+item["nH"]*3+item["nS"]) / (item["nB"]+item["nH"]+item["nS"])
        
        return data
    
    def _get_ratings_data(self):
        if not hasattr(self, "_ratings_data"):
            self._ratings_data = requests.get(
                url = f"{self._base_url}getData/",
                headers = TIPRANKS_HEADERS,
                params = {"name": self.ticker}
            ).json()
        return self._ratings_data