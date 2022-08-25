import requests
from finance_data.utils import HEADERS

def get_companies() -> list:
    items = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS).json()
    items = [
        {
            "cik": item["cik_str"],
            "ticker": item["ticker"],
            "name": item["title"],
        }
        for _, item in items.items()
    ]
    return items

def get_mutualfunds() -> list:
    items = requests.get("https://www.sec.gov/files/company_tickers_mf.json", headers=HEADERS).json()["data"]
    items = [
        {
            "cik": item[0],
            "ticker": item[3],
            "series_identifier": item[1],
            "class_identifier": item[2],
        }
        for item in items
    ]
    return items