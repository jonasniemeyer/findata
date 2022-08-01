import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from finance_data.utils import TIPRANKS_HEADERS, HEADERS

class TipranksAnalystReader:
    _base_url = "https://www.tipranks.com/experts/analysts/"
    
    def __init__(self, name) -> None:
        self.name = name
    
    def ratings(self, timestamps=False):
        table = self._get_analyst_data().find("div", {"data-sc": "StockCoverage"})
        rows = table.find_all("div", {"class": "rt-tr-group"})
        ratings = []
        
        for row in rows:
            cells = row.find("div", {"class": "rt-tr"}, recursive=False).find_all("div", recursive=False)
            assert len(cells) == 9
            ticker = cells[1].find("div", recursive=False).find("div", recursive=False).find("a").text
            name = cells[1].find("div", recursive=False).find("span", recursive=False).text
            date = cells[2].find("time").get("datetime")
            date = pd.to_datetime(date)
            if timestamps:
                date = int(pd.to_datetime(date.date()).timestamp())
            else:
                date = date.date().isoformat()
            rating = cells[3].find("span").text
            change = cells[4].find("span").text
            price = cells[5].find("div")
            if price is None:
                price = None
            else:
                price = price.text.split("(")[0].replace("$", "").strip()
            no_ratings = int(cells[8].find("span").text)
            ratings.append(
                {
                   "ticker": ticker,
                    "name": name,
                    "date": date,
                    "rating": rating,
                    "change": change,
                    "price_target": price,
                    "no_ratings": no_ratings
                }
            )
        
        return ratings
    
    def profile(self):        
        return {**self._get_profile(), **self._get_coverage_information(), **self._get_rating_distribution()}
    
    def _get_analyst_data(self):
        if not hasattr(self, "_analyst_data"):
            name_encoded = self.name.lower().replace(" ", "-")
            self._analyst_data = requests.get(
                url = f"{self._base_url}{name_encoded}",
                headers = HEADERS
            ).text
            self._analyst_data = BeautifulSoup(self._analyst_data, "lxml")
        
        return self._analyst_data
    
    def _get_coverage_information(self):
        information = self._get_analyst_data().find("div", {"data-sc": "Information"}).find_all("div", recursive=False)[1].find_all("div")
        
        assert information[0].find_all("span")[0].text == "Main Sector:"
        assert information[1].find_all("span")[0].text == "Geo Coverage:"
        sector = information[0].find_all("span")[1].text
        country = information[1].find_all("span")[1].text
        
        return {"sector": sector, "country": country}
    
    def _get_profile(self):
        profile_divs = self._get_analyst_data().find("div", {"data-sc": "Profile"}).find_all("div", recursive=False)[1].find_all("div", recursive=False)

        personal = profile_divs[0]
        performance = profile_divs[1].find_all("div", recursive=False)[1]

        name = personal.find("h1").text
        company = personal.find("span").text
        analyst_rank, total_analysts = re.findall(
            "Ranked #([0-9,]+) out of ([0-9,]+) Analysts on TipRanks",
            personal.find_all("div", recursive=False)[1].find_all("div", recursive=False)[1].text
        )[0]
        analyst_rank = int(analyst_rank.replace(",", ""))
        total_analysts = int(total_analysts.replace(",", ""))
        image_url = personal.find("img").get("src")

        positive_recommendations, total_recommendations = re.findall(
            "([0-9]+) out of ([0-9]+) Profitable Transactions",
            performance.find_all("div", recursive=False)[0].find_all("div", recursive=False)[2].text
        )[0]
        positive_recommendations = int(positive_recommendations)
        total_recommendations = int(total_recommendations)
        success_rate = round(positive_recommendations/total_recommendations, 4)
        average_rating_return = performance.find_all("div", recursive=False)[2].find_all("div", recursive=False)[1].find("span").text
        average_rating_return = round(float(average_rating_return.replace("%", "")) / 100, 4)
        
        dct = {
            "name": name,
            "company": company,
            "image_url": image_url,
            "rank": analyst_rank,
            "total_analysts": total_analysts,
            "positive_recommendations": positive_recommendations,
            "total_recommendations": total_recommendations,
            "success_rate": success_rate,
            "average_rating_return": average_rating_return
        }
        
        return dct
    
    def _get_rating_distribution(self):
        rating_distribution = self._get_analyst_data().find("div", {"data-sc": "StockRating"}).find_all("div", recursive=False)[1].find_all("div")[1].find_all("div", recursive=False)
        
        distribution = {}
        for tag in rating_distribution:
            percentage, rating = tag.find("div").text.split()
            percentage = round(float(percentage.replace("%", "")) / 100, 2)
            distribution[rating.lower()] = percentage
        
        return distribution


class TipranksStockReader:
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
                "consensus_score": round(item["consensusScore"], 2),
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
    
    def blogger_sentiment(self):
        data = self._get_ratings_data()["bloggerSentiment"]
        data = {
            "positive": data["bullishCount"],
            "neutral": data["neutralCount"],
            "negative": data["bearishCount"],
            "average": round(data["avg"], 2)
        }
        return data
    
    def covering_analysts(self, include_retail=False, timestamps=False, sorted_by="name"):
        sort_variables = (
            "name",
            "company",
            "stock_success_rate",
            "average_rating_return_stock",
            "total_recommendations_stock",
            "positive_recommendations_stock",
            "price_target",
            "rank",
            "successful_recommendations",
            "total_recommendations",
            "average_rating_return",
            "stars",
        )
        if sorted_by not in (sort_variables):
            raise ValueError(f"sorting variable has to be in {sort_variables}")

        data = self._get_ratings_data()["experts"]
        data = [
            {
                "name": item["name"],
                "company": item["firm"],
                "image_url": (
                    None if item['expertImg'] is None 
                    else f"https://cdn.tipranks.com/expert-pictures/{item['expertImg']}_tsqr.jpg"
                ),
                "stock_success_rate": round(item["stockSuccessRate"], 4),
                "average_rating_return_stock": round(item["stockAverageReturn"], 4),
                "total_recommendations_stock": item["stockTotalRecommendations"],
                "positive_recommendations_stock": item["stockGoodRecommendations"],
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
                    "percentage_successful_recommendations": round(item["rankings"][0]["gRecs"] / item["rankings"][0]["tRecs"], 4),
                    "average_rating_return": round(item["rankings"][0]["avgReturn"], 4),
                    "stars": round(item["rankings"][0]["originalStars"], 1)
                }
            } for item in data
        ]
        
        if not include_retail:
            data = [item for item in data if item["consensus_analyst"] is True]
        
        desc = False if sorted_by in ("name", "company", "rank") else True
        if sorted_by in (
            "rank",
            "successful_recommendations",
            "total_recommendations",
            "percentage_successful_recommendations",
            "average_rating_return",
            "stars"
        ):
            data = sorted(data, key=lambda x: (x["analyst_ranking"][sorted_by] is None, x["analyst_ranking"][sorted_by]), reverse=desc)
        elif sorted_by == "price_target":
            data = sorted(data, key=lambda x: (x["ratings"][0][sorted_by] is None, x["ratings"][0][sorted_by]), reverse=desc)
        else:
            data = sorted(data, key=lambda x: (x[sorted_by] is None, x[sorted_by]), reverse=desc)

        return data
    
    def insider_trades(self, timestamps=False, sorted_by="name"):
        sort_variables = ("name", "amount", "shares", "report_date")
        if sorted_by not in sort_variables:
            raise ValueError(f"sorting variable has to be in {sort_variables}")

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

        desc = True if sorted_by in ("amount", "shares", "report_date") else False
        data["insiders"] = sorted(data["insiders"], key=lambda x: (x[sorted_by] is None, x[sorted_by]), reverse=desc)

        return data
    
    def institutional_ownership(self, sorted_by="name"):
        sort_variables = (
            "name",
            "company",
            "stars",
            "rank",
            "value",
            "change",
            "percentage_of_portfolio"
        )
        if sorted_by not in sort_variables:
            raise ValueError(f"sorting variable has to be in {sort_variables}")

        data = self._get_ratings_data()["hedgeFundData"]["institutionalHoldings"]
        data = [
            {
                "name": item["managerName"],
                "company": item["institutionName"],
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
        
        desc = False if sorted_by in ("name", "company", "rank") else True
        data = sorted(data, key=lambda x: (x[sorted_by] is None, x[sorted_by]), reverse=desc)
        
        return data

    def institutional_ownership_trend(self, timestamps=False):
        data_raw = self._get_ratings_data()["hedgeFundData"]["holdingsByTime"]
        data = {}
        for item in data_raw:
            date = pd.to_datetime(item["date"]).date()
            date = int(pd.to_datetime(date).timestamp()) if timestamps else date.isoformat()
            data[date] = item["holdingAmount"]
        
        return data
    
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
                    "hold": item["neutral"],
                    "sell": item["sell"],
                    "average": round(
                            (item["buy"]*5+item["neutral"]*3+item["sell"]*1) / (item["buy"]+item["neutral"]+item["sell"]), 2
                        ) if item["buy"]+item["neutral"]+item["sell"] != 0 else None,
                    "count": item["all"]
                } for item in data["counts"]
            ],
            "sector_average_news_score": data["sectorAverageNewsScore"]
        }
        
        return data
    
    def peers(self):
        data = self._get_ratings_data()["similarStocks"]
        data = [
            {
                "ticker": item["ticker"],
                "name": item["name"],
                "buy": item["consensusData"][0]["nB"],
                "hold": item["consensusData"][0]["nH"],
                "sell": item["consensusData"][0]["nS"],
                "average": (
                    round(
                        (item["consensusData"][0]["nB"]*5+item["consensusData"][0]["nH"]*3+item["consensusData"][0]["nS"])
                        /(item["consensusData"][0]["nB"]+item["consensusData"][0]["nH"]+item["consensusData"][0]["nS"]),
                        2
                    )
                ) if item["consensusData"][0]["nB"]+item["consensusData"][0]["nH"]+item["consensusData"][0]["nS"] != 0 else None,
                "average_price_target": item["consensusData"][0]["priceTarget"]
            }
            for item in data
        ]
        return data
    
    def profile(self):
        company_data = self._get_ratings_data()["companyData"]
        data = {
            "isin": self._get_ratings_data()["isin"],
            "description": self._get_ratings_data()["description"],
            "industry": company_data["industry"],
            "sector": company_data["sector"],
            "ceo": company_data["ceo"],
            "employees": company_data["employees"],
            "website": company_data["website"],
            "address": company_data["companyAddress"]
        }
        return data
    
    def recommendation_trend(self, timestamps=False):
        data_raw = self._get_ratings_data()
        data = {"all_analysts": {}, "best_analysts": {}}
        
        for dataset, key in zip(
            ("all_analysts", "best_analysts"),
            ("consensusOverTime", "bestConsensusOverTime")
        ):
            for item in data_raw[key]:
                date = pd.to_datetime(item["date"]).date()
                date = int(pd.to_datetime(date).timestamp()) if timestamps else date.isoformat()

                data[dataset][date] = data[dataset].get(date, {})
                data[dataset][date]["consensus_rating"] = item["consensus"]
                data[dataset][date]["buy"] = item["buy"]
                data[dataset][date]["hold"] = item["hold"]
                data[dataset][date]["sell"] = item["sell"]
                data[dataset][date]["count"] = item["buy"] + item["hold"] + item["sell"]
                data[dataset][date]["average"] = (
                    round((item["buy"]*5+item["hold"]*3+item["sell"]) / data[dataset][date]["count"], 2)
                ) if data[dataset][date]["count"] != 0 else None
                data[dataset][date]["average_price_target"] = round(item["priceTarget"], 2)
        
        return data
    
    def recommendation_trend_breakup(self, sorted_by="star", timestamps=False):
        if sorted_by not in ("star", "date"):
            raise ValueError(f"sorting variable has to be 'star' or 'date'")
        data_raw = self._get_ratings_data()["consensuses"]
        data = {}
        
        for item in data_raw:
            star = item["mStars"]
            date = pd.to_datetime(item["d"])
            date = (
                int(pd.to_datetime(date.date()).timestamp()) if timestamps 
                else date.date().isoformat()
            )

            data[date] = data.get(date, {})
            data[date][star] = data.get(star, {})
            data[date][star]["buy"] = item["nB"]
            data[date][star]["hold"] = item["nH"]
            data[date][star]["sell"] = item["nS"]
        
        for date in data:
            data[date]["all"] = data[date][1]
            for star in range(1, 5):
                data[date][star] = {key: data[date][star][key] - data[date][star+1][key] for key in ("buy", "hold", "sell")}
        
        for date in data:
            for star in data[date]:
                data[date][star]["count"] = data[date][star]["buy"] + data[date][star]["hold"] + data[date][star]["sell"]
                if data[date][star]["count"] != 0:
                    data[date][star]["average"] = (
                            round((data[date][star]["buy"]*5+data[date][star]["hold"]*3+data[date][star]["sell"])
                            / (data[date][star]["buy"]+data[date][star]["hold"]+data[date][star]["sell"]), 2)
                        )
                else:
                    data[date][star]["average"] = None
        
        if sorted_by == "star":
            temp_dct = data.copy()
            data = {1: {}, 2: {}, 3:{}, 4:{}, 5:{}, "all": {}}
            for date in temp_dct:
                for star in temp_dct[date]:
                    data[star][date] = temp_dct[date][star]
        
        return data
        
    def _get_ratings_data(self):
        if not hasattr(self, "_ratings_data"):
            self._ratings_data = requests.get(
                url = f"{self._base_url}getData/",
                headers = TIPRANKS_HEADERS,
                params = {"name": self.ticker}
            ).json()
        return self._ratings_data