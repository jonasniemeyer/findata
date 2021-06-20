class TickerError(ValueError):
    pass

class DatasetError(KeyError):
    pass

_headers = {
        "Connection": "keep-alive",
        "Expires": "-1",
        "Upgrade-Insecure-Requests": "-1",
        "User-Agent": (
            "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        ),
    }
