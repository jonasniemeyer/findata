import requests
from bs4 import BeautifulSoup
import pandas as pd
from finance_data.utils import HEADERS

def margin_debt(timestamps=False) -> dict:
    dataset_url = "https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics"
    data = {
        "combined new": [],
        "finra old": [],
        "nyse old": [],
        "combined old": []
    }
    
    html = requests.get(url=dataset_url, headers=HEADERS).text
    
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
                date = pd.to_datetime(date.replace("Sept", "Sep"), format="%b-%y")
            except:
                date = pd.to_datetime(date, format="%B-%y")
            datapoint = (date, *values)
            data[key].append(datapoint)
        data[key] = pd.DataFrame(
            data = data[key],
            columns = ["month", "debit", "credit cash accounts", "credit margin accounts"] if len(data[key][0]) == 4 \
            else ["month", "debit", "credit"]
        )
        data[key].set_index("month", inplace=True, drop=True)
        data[key].sort_index(inplace=True)
        if timestamps:
            data[key].index = [int(date.timestamp()) for date in data[key].index]
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

def shiller_cape(timestamps=False) -> pd.DataFrame:
    df = pd.read_excel(
        io="http://www.econ.yale.edu/~shiller/data/ie_data.xls",
        sheet_name="Data",
        skiprows=(0,1,2,3,4,5,7),
        skipfooter=1,
        index_col=0
    )
    df.index = [
        pd.to_datetime(f"{str(item)[:4]}-{str(item)[-2:]}-01") if len(str(item)) == 7
        else pd.to_datetime(f"{str(item)[:4]}-10-01")
        for item in df.index
    ]
    df = df.drop(["Date  ", "Unnamed: 13", "Unnamed: 15"], axis=1)
    df = df.rename(
        columns = {
            "Comp.": "Index",
            "Dividend": "Dividends",
            "Index": "CPI",
            "Interest": "10-Year Interest Rate",
            "Real": "Real Index",
            "Real.1": "Real Dividends",
            "Return": "Real Total Price Return",
            "Real.2": "Real Earnings",
            "Scaled": "Real TR Scaled Earnings",
            "P/E10 or": "CAPE",
            "TR P/E10 or": "Total Price Return CAPE",
            "CAPE": "Excess CAPE Yield",
            "Bond": "Total Bond Return",
            "Bond.1": "Real Total Bond Return",
            "Annualized Stock": "10-Year Annualized Real Stock Return",
            "Annualized Bonds": "10-Year Annualized Real Bond Return",
            "Excess Annualized ": "10-Year Annualized Excess Stock Return"
        }
    )
    if timestamps:
        df.index = [int(date.timestamp()) for date in df.index]
    return df