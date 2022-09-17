import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from finance_data.utils import HEADERS

class FinvizReader:
    _base_url = "https://finviz.com/quote.ashx?t={}"
    
    def __init__(self, ticker):
        self._ticker = ticker.upper()
        self._html = requests.get(
            url=self._base_url.format(self._ticker),
            headers=HEADERS
        ).text
        if "This IP address has performed an unusual high number of requests and has been temporarily rate limited. If you believe this to be in error, please contact us." in self._html:
            raise PermissionError("Requests have been rate limited")
        self._soup = BeautifulSoup(self._html, "lxml")
    
    def analyst_recommendations(self, timestamps=False) -> list:
        table = self._soup.find_all("table", {"class": "fullview-ratings-outer"})
        if len(table) == 1:
            table = table[0]
        else:
            return []
        recommendations = []
        rows = table.find_all("tr")
        for row in rows:
            row = row.find_all("tr")
            if len(row) != 0:
                row = row[0]
                cells = row.find_all("td")
                date = pd.to_datetime(cells[0].text)
                if timestamps:
                    date = int(date.timestamp())
                else:
                    date = date.date().isoformat()
                change = cells[1].text.strip()
                company = cells[2].text.strip()
                ratings = cells[3].text.split("→")
                prices = cells[4].text.replace("$", "").split("→")
                
                assert change in ("Reiterated", "Initiated", "Resumed", "Upgrade", "Downgrade")
                if change in ("Reiterated", "Resumed"):
                    rating_new = ratings[0].strip()
                    rating_old = ratings[0].strip()
                elif change == "Initiated":
                    rating_new = ratings[0].strip()
                    rating_old = None
                else:
                    rating_old = ratings[0].strip()
                    rating_new = ratings[1].strip()
                
                if change == "Initiated":
                    price_old = ""
                    price_new = prices[0]
                else:
                    price_old = prices[0]
                    if len(prices) == 1:
                        price_new = price_old
                    else:
                        price_new = prices[1]
                
                price_old = None if price_old == "" else float(price_old)
                price_new = None if price_new == "" else float(price_new)
                
                recommendations.append(
                    {
                        "date": date,
                        "company": company,
                        "change": change,
                        "rating_old": rating_old,
                        "rating_new": rating_new,
                        "price_old": price_old,
                        "price_new": price_new
                    }
                )
        return recommendations

    def insider_trades(self) -> list:
        table = self._soup.find_all("table", {"class": "body-table"})
        if len(table) == 1:
            table = table[0]
        else:
            return []
        trades = []
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            name = cells[0].text.strip().title()
            position = cells[1].text.strip()
            date = cells[2].text.strip()
            transaction = cells[3].text.strip()
            price = float(cells[4].text.strip())
            shares = int(cells[5].text.strip().replace(",", ""))
            value = int(cells[6].text.strip().replace(",", ""))
            url = cells[8].find_all("a")[0].get("href").strip()
            trades.append(
                {
                    "name": name,
                    "position": position,
                    "date": date,
                    "transaction": transaction,
                    "shares": shares,
                    "value": value,
                    "price": price,
                    "url": url
                    
                }
            )
        return trades
    
    def news(self, timestamps=False) -> list:
        table = self._soup.find_all("table", {"class": "fullview-news-outer"})
        if len(table) == 1:
            table = table[0]
        else:
            return []
        news = []
        rows = table.find_all("tr")
        for row in rows:
            datetime = row.find_all("td")[0].text.strip()
            if len(datetime) > 7:
                date = pd.to_datetime(datetime).date()
                if timestamps:
                    date_ = int(pd.to_datetime(date).timestamp())
                else:
                    date_ = date.isoformat()
            source = row.find_all("div")[2].text.strip()
            source = re.sub("\s*[\-+]?[0-9]{,3}\.?[0-9]{2}%", "", source)
            title = row.find_all("td")[1].find_all("a")[0].text.strip()
            url = row.find_all("td")[1].find_all("a")[0].get("href").strip()
            
            news.append(
                {
                    "date": date_,
                    "source": source,
                    "title": title,
                    "url": url
                }
            )
        return news