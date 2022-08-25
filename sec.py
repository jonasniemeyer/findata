import requests
from finance_data.utils import HEADERS

def sec_companies() -> list:
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

def sec_mutualfunds() -> list:
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


class _SECFiling:
    pass

class Filing3(_SECFiling):
    pass

class Filing4(Filing3):
    pass

class Filing5(Filing4):
    pass

class Filing13G(_SECFiling):
    pass

class Filing13D(Filing13G):
    pass

class Filing13F(_SECFiling):
    pass

class FilingNPORT(_SECFiling):
    pass