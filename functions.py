import requests
from bs4 import BeautifulSoup
import datetime as dt
import pandas as pd
from finance_data.utils import HEADERS

def margin_debt():
    dataset_url = "https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics"
    data = {
        "combined new": [],
        "finra old": [],
        "nyse old": [],
        "combined old": []
    }
    
    html = requests.get(url = dataset_url, headers = HEADERS).text
    
    finra = html.index("FINRA Statistics (shown in $ millions)")
    nyse = html.index("NYSE Statistics (shown in $ millions)")
    combined = html.index("FINRA and NYSE Combined Statistics (shown in $ millions)")
    
    data_new = html[:finra]
    data_finra = html[finra:nyse]
    data_nyse = html[nyse:combined]
    data_combined = html[combined:]
    
    for data_slice, key in zip(
        (
            data_new,
            data_finra,
            data_nyse,
            data_combined
        ),
        data
    ):
        soup = BeautifulSoup(data_slice, "lxml")
        rows = soup.find_all("tr")
        rows = [row.find_all("td") for row in rows if len(row.find_all("td")) > 1]
        rows = [
            [item.text for item in sublist]
            for sublist in rows
        ]
        for row in rows:
            date, *values = row
            values = [int(item.replace(",", "")) for item in values]
            try:
                date = dt.datetime.strptime(date.replace("Sept", "Sep"), "%b-%y").date()
            except:
                date = dt.datetime.strptime(date, "%B-%y").date()
            datapoint = (date, *values)
            data[key].append(datapoint)
        data[key] = pd.DataFrame(
            data = data[key],
            columns = ["month", "debit", "credit cash accounts", "credit margin accounts"] if len(data[key][0]) == 4 \
            else ["month", "debit", "credit"]
        )
        data[key].set_index("month", inplace=True, drop=True)
        data[key].sort_index(inplace=True)
    new_aggregated = pd.DataFrame()
    new_aggregated["debit"] = data["combined new"]["debit"]
    new_aggregated["credit"] = data["combined new"]["credit cash accounts"] + data["combined new"]["credit margin accounts"]
    data["combined full"] = pd.concat([new_aggregated, data["combined old"]]).sort_index()
    data = {
        "combined full": data["combined full"] * 1_000_000,
        "combined new": data["combined new"] * 1_000_000,
        "combined old": data["combined old"] * 1_000_000,
        "finra old": data["finra old"] * 1_000_000,
        "nyse old": data["nyse old"] * 1_000_000
    }
    return data

