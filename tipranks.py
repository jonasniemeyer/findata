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
                "consensus_score": round(item["consensusScore"], 4),
                "sector": item["sector"],
                "market_cap": item["marketCap"],
                "buy": item["buy"],
                "hold": item["hold"],
                "sell": item["sell"],
                "consensus_rating": item["rating"],
                "price_target": item["priceTarget"],
                "latest_rating": (
                    int(pd.to_datetime(pd.to_datetime(item["lastRatingDate"]).date()).timestamp()) if timestamps
                    else pd.to_datetime(item["lastRatingDate"]).date().isoformat()
                )
            } for item in data
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
                } for item in data["sector"]
            ],
            "sector_average_sentiment": data["sectorAverageBullishPercent"],
            "news_score": data["score"],
            "articles": [
                {
                    "week": (
                        int(pd.to_datetime(pd.to_datetime(item["weekStart"]).date()).timestamp()) if timestamps
                        else pd.to_datetime(item["weekStart"]).date().isoformat()
                    ),
                    "buy": item["buy"],
                    "neutral": item["neutral"],
                    "sell": item["sell"],
                    "total": item["all"]
                } for item in data["counts"]
            ],
            "sector_average_news_score": data["sectorAverageNewsScore"]
        }
        
        return data

    def recommendation_trend_breakup(self, sorted_by="stars", timestamps=False):
        data_raw = self._get_ratings_data()["consensuses"]
        data = {}
        
        for item in data_raw:
            stars = item["mStars"]
            date = pd.to_datetime(item["d"])
            date = (
                int(pd.to_datetime(date.date()).timestamp()) if timestamps 
                else date.date().isoformat()
            )
            
            prim_k = stars if sorted_by == "stars" else date
            sec_k = date if sorted_by == "stars" else stars
            
            data[prim_k] = data.get(prim_k, {})
            data[prim_k][sec_k] = data.get(sec_k, {})
            data[prim_k][sec_k]["consensus_rating"] = item["rating"]
            data[prim_k][sec_k]["buy"] = item["nB"]
            data[prim_k][sec_k]["hold"] = item["nH"]
            data[prim_k][sec_k]["sell"] = item["nS"]
            data[prim_k][sec_k]["average"] = (
                round((item["nB"]*5+item["nH"]*3+item["nS"]) / (item["nB"]+item["nH"]+item["nS"]), 2)
            )
        
        return data
    
    def recommendation_trend(self, timestamps=False):
        data_raw = self._get_ratings_data()
        data_best = self._get_ratings_data()
        data = {"all": {}, "best": {}}
        
        for dataset, key in zip(
            ("all", "best"),
            ("consensusOverTime", "bestConsensusOverTime")
        ):
            for item in data_raw[key]:
                date = pd.to_datetime(item["date"]).date()
                date = int(pd.to_timestamp(date).timestamp()) if timestamps else date.isoformat()

                data[dataset][date] = data[dataset].get(date, {})
                data[dataset][date]["consensus_rating"] = item["consensus"]
                data[dataset][date]["buy"] = item["buy"]
                data[dataset][date]["hold"] = item["hold"]
                data[dataset][date]["sell"] = item["sell"]
                data[dataset][date]["average"] = (
                    round((item["buy"]*5+item["hold"]*3+item["sell"]) / (item["buy"]+item["hold"]+item["sell"]), 2)
                )
                data["all"][date]["average_price_target"] = round(item["priceTarget"], 2)
        
        return data
    
    def covering_analysts(self, include_retail=False, timestamps=False):
        data = self._get_ratings_data()["experts"]
        data = [
            {
                "name": item["name"],
                "firm": item["firm"],
                "image_url": (
                    None if item['expertImg'] is None 
                    else f"https://cdn.tipranks.com/expert-pictures/{item['expertImg']}_tsqr.jpg"
                ),
                "stock_success_rate": round(item["stockSuccessRate"], 4),
                "average_rating_return": round(item["stockAverageReturn"], 4),
                "total_recommendations": item["stockTotalRecommendations"],
                "positive_recommendations": item["stockGoodRecommendations"],
                "consensus_analyst": item["includedInConsensus"],
                "ratings": [
                    {
                        "date": (
                            int(pd.to_datetime(pd.to_datetime(rating["date"]).date()).timestamp()) if timestamps 
                            else pd.to_datetime(rating["date"]).date().isoformat()
                        ),
                        "price_target": rating["priceTarget"],
                        "news_url": rating["url"],
                        "news_title": rating["quote"]["title"]
                    } for rating in item["ratings"]
                ],
                "analyst_ranking": {
                    "rank": item["rankings"][0]["lRank"],
                    "successful_recommendations": item["rankings"][0]["gRecs"],
                    "total_recommendations": item["rankings"][0]["tRecs"],
                    "average_rating_return": round(item["rankings"][0]["avgReturn"], 4),
                    "stars": round(item["rankings"][0]["originalStars"], 1)
                }
            } for item in data
        ]
        
        if not include_retail:
            data = [item for item in data if item["consensus_analyst"] is True]
        
        return data
    
    def institutional_ownership(self, sorted_by="name"):
        data = self._get_ratings_data()["hedgeFundData"]["institutionalHoldings"]
        data = [
            {
                "name": item["managerName"],
                "firm": item["institutionName"],
                "stars": round(item["stars"], 1),
                "rank": item["rank"],
                "ranked_institutions": item["totalRankedInstitutions"],
                "value": item["value"],
                "change": round(item["change"]/100, 4),
                "percentage_of_portfolio": round(item["percentageOfPortfolio"], 4),
                "image_url": (
                    None if item["imageURL"] is None 
                    else f"https://cdn.tipranks.com/expert-pictures/{item['imageURL']}_tsqr.jpg"
                )
            }
            for item in data
        ]
        
        desc = True if sorted_by in ("stars", "value", "change", "percentage_of_portfolio") else False            
        data = sorted(data, key=lambda x: x[sorted_by], reverse=desc)
        
        return data

    def institutional_ownership_trend(self, timestamps=False):
        data_raw = self._get_ratings_data()["hedgeFundData"]["holdingsByTime"]
        data = {}
        for item in data_raw:
            date = pd.to_datetime(item["date"]).date()
            date = int(pd.to_datetime(date).timestamp()) if timestamps else date.isoformat()
            data[date] = item["holdingAmount"]
        
        return data
    
    def blogger_sentiment(self):
        data = self._get_ratings_data()["bloggerSentiment"]
        data = {
            "positive": data["bullishCount"],
            "neutral": data["neutralCount"],
            "negative": data["bearishCount"],
            "average": data["avg"]
        }
        return data
    
    def insider_trades(self, timestamps=False):
        insiders = self._get_ratings_data()["insiders"]
        trades_sum = self._get_ratings_data()["insiderslast3MonthsSum"]
        data = {"insiders": [], "insider_trades_last_3_months": trades_sum}
        data["insiders"] = [
            {
                "name": item["name"],
                "company": item["company"],
                "officer": item["isOfficer"],
                "director": item["isDirector"],
                "title": item["officerTitle"],
                "amount": item["amount"],
                "shares": item["numberOfShares"],
                "report_date": (
                    int(pd.to_datetime(pd.to_datetime(item["rDate"]).date()).timestamp()) if timestamps 
                    else pd.to_datetime(item["rDate"]).date().isoformat()
                ),
                "file_url": item["link"],
                "image_url": (
                    None if item["expertImg"] is None 
                    else f"https://cdn.tipranks.com/expert-pictures/{item['expertImg']}_tsqr.jpg"
                )
            }
            for item in insiders
        ]
        return data
    
    def _get_ratings_data(self):
        if not hasattr(self, "_ratings_data"):
            self._ratings_data = requests.get(
                url = f"{self._base_url}getData/",
                headers = TIPRANKS_HEADERS,
                params = {"name": self.ticker}
            ).json()
        return self._ratings_data