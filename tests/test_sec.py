import re
import pytest
from finance_data.sec import _SECFiling
from finance_data import (
    latest_sec_filings,
    sec_companies,
    sec_mutualfunds,
    Filing13G,
    Filing13D,
    Filing13F,
    FilingNPORT,
    Filing3,
    Filing4,
    Filing5
)

def test_sec_companies():
    companies = sec_companies()
    for item in companies:
        for key in item.keys():
            assert key in ("cik", "name", "ticker")
        assert isinstance(item["cik"], int)
        assert isinstance(item["name"], str)
        assert isinstance(item["ticker"], str)

def test_sec_mutualfunds():
    funds = sec_mutualfunds()
    for item in funds:
        for key in item.keys():
            assert key in ("ticker", "class_cik", "series_cik", "entity_cik")
        assert isinstance(item["ticker"], str)
        assert isinstance(item["class_cik"], str)
        assert isinstance(item["series_cik"], str)
        assert isinstance(item["entity_cik"], int)

def test_latest_sec_filings():
    filings = latest_sec_filings(start="2022-12-22")
    for filing in filings:
        for key in filing.keys():
            assert key in ("name", "cik", "form_type", "url", "accession_number", "accepted", "date_filed", "file_number", "film_number")
        assert isinstance(filing["name"], str)
        assert isinstance(filing["cik"], int)
        assert isinstance(filing["form_type"], str)
        assert isinstance(filing["url"], str) and filing["url"].endswith(".txt")
        assert isinstance(filing["accession_number"], str)
        assert isinstance(filing["accepted"], str) and len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", filing["accepted"])) == 1
        assert isinstance(filing["date_filed"], str) and len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", filing["date_filed"])) == 1 
        assert filing["file_number"] is None or isinstance(filing["file_number"], str)
        assert filing["film_number"] is None or isinstance(filing["film_number"], int)
    
    filings = latest_sec_filings(start="2022-12-22", timestamps=True)
    for filing in filings:
        assert isinstance(filing["accepted"], int)
        assert isinstance(filing["date_filed"], int)

def search_sec_filings():
    pass

class TestSECFiling:
    pass


class TestFilingNPORT:
    @classmethod
    def setup_class(cls):
        cls.file = None

    def test_general_information(self):
        pass

    def test_fund_information(self):
        pass

    def test_portfolio(self):
        for var in (None, "name", "market_value", "quantity", "percentage", "payoff_direction"):
            portfolio = self.file.portfolio(sorted_by=var)
        
        with pytest.raises(ValueError):
            self.file.portfolio(sorted_by="foo")

    def test_miscellaneous_securities(self):
        pass

    def test_explanatory_notes(self):
        pass

    def test_signature(self):
        pass

    def test_exhibits(self):
        pass

    def test_debt_security(self):
        pass

    def test_debt_convertible(self):
        pass

    def test_derivative_future(self):
        pass

    def test_derivative_currency_forward(self):
        pass

    def test_derivative_swap(self):
        pass

    def test_derivative_option(self):
        pass

    def test_derivative_warrant(self):
        pass

    def test_derivative_swaption(self):
        pass

    def test_lending_information(self):
        pass