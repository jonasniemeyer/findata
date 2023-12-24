import configparser
import os
from copy import deepcopy
from pathlib import Path

class TickerError(ValueError):
    pass

class DatasetError(KeyError):
    pass

HEADERS = {
    "Connection": "keep-alive",
    "Expires": "-1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    )
}
HEADERS_FAKE = deepcopy(HEADERS)
HEADERS_FAKE["User-Agent"] = "JohnDoe@gmail.com"

TIPRANKS_HEADERS = deepcopy(HEADERS)
YAHOO_HEADERS = deepcopy(HEADERS)

if "private.cfg" in os.listdir(Path(__file__).parent):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(rf"{Path(__file__).parent}\private.cfg")
    CHROMEDRIVER_PATH = cfg.get("PATHS", "chromedriver")
    FRED_API_KEY = cfg.get("KEYS", "fred_api_key")
    TIPRANKS_HEADERS["cookie"] = cfg.get("COOKIES", "tipranks_cookies")
    YAHOO_CRUMB = cfg.get("KEYS", "yahoo_crumb")
    YAHOO_HEADERS["cookie"] = cfg.get("COOKIES", "yahoo_cookies")
else:
    FRED_API_KEY = None
    CHROMEDRIVER_PATH = f"{Path(__file__).parents[3]}/chromedriver.exe"
    YAHOO_CRUMB = None

_companies = None
_mutualfunds = None