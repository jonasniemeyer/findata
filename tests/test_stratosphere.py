import datetime as dt
from finance_data import StratosphereReader

def test_fund_letters():
    letters = StratosphereReader.fund_letters()
    for letter in letters:
        assert isinstance(letter["company"], str)
        assert dt.date.fromisoformat(letter["date"])
        assert isinstance(letter["year"], int)
        assert letter["quarter"] in (1, 2, 3, 4)
        assert isinstance(letter["url"], str)
    
    letters = StratosphereReader.fund_letters(timestamps=True)
    for letter in letters:
        assert isinstance(letter["date"], int)