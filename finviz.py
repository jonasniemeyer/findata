import requests
from bs4 import BeautifulSoup
from utils import HEADERS

class FinvizReader:
    _base_url = "https://finviz.com/quote.ashx?t={}"
    
    def __init__(self, ticker):
        self._ticker = ticker
        self._html = requests.get(
            url=self._base_url.format(self._ticker),
            headers=HEADERS
        ).text
        self._soup = BeautifulSoup(self._html)
    
    def analyst_recommendations(self, timestamps=False):
        table = self._soup.find_all("table", {"class": "fullview-ratings-outer"})
        if table:
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
                change = cells[1].text
                company = cells[2].text
                ratings = cells[3].text.split("→")
                prices = cells[4].text.replace("$", "").split("→")
                
                if len(ratings) == 1:
                    rating_old = ""
                    rating_new = ratings[0].strip()
                else:
                    rating_old = ratings[0].strip()
                    rating_new = ratings[1].strip()
                price_old = prices[0].strip()
                if len(prices) == 1:
                    price_old = ""
                    price_new = prices[0].strip()
                else:
                    price_new = prices[0].strip()
                    price_new = prices[1].strip()
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
        

    def insider_trades(self):
        pass
    
    def news(self):
        pass