class TickerError(ValueError):
    pass

class DatasetError(KeyError):
    pass

_headers = {
        "Connection": "keep-alive",
        "Expires": "-1",
        "Upgrade-Insecure-Requests": "-1",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
        ),
    }