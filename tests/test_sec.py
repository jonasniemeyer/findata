import re
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
    filings = latest_sec_filings(start="2022-01-01")
    for item in filings:
        for key in item.keys():
            assert key in ("name", "cik", "form_type", "url", "accession_number", "accepted", "date_filed", "file_number", "film_number")
        assert isinstance(item["name"], str)
        assert isinstance(item["cik"], int)
        assert isinstance(item["form_type"], str)
        assert isinstance(item["url"], str) and item["url"].endswith(".txt")
        assert isinstance(item["accession_number"], str)
        assert isinstance(item["accepted"], str) and len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", item["accepted"])) == 1
        assert isinstance(item["date_filed"], str) and len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", item["date_filed"])) == 1 
        assert item["file_number"] is None or isinstance(item["file_number"], str)
        assert item["film_number"] is None or isinstance(item["film_number"], int)

def search_sec_filings():
    pass

class TestSECFiling:
    def xml_file(self):
        pass
    
    def text_file(self):
        pass


class TestFiling13G:
    pass


class TestFiling13D:
    pass


class TestFiling13F_xml:
    def test_no_prefix(self):
        pass

    def test_n1_prefix(self):
        pass

    def test_ns1_prefix(self):
        pass

    def test_aggregate_portfolio(self):
        pass


class TestFiling13F_text:
    pass


class TestFilingNPORT:
    def test_attributes(self):
        pass

    def test_general_information(self):
        pass

    def test_fund_information(self):
        pass

    def test_portfolio(self):
        pass

    def test_miscellaneous_securities(self):
        pass

    def test_explanatory_notes(self):
        pass

    def test_signature(self):
        pass

    def test_exhibits(self):
        pass


class TestFiling3:
    pass


class TestFiling4:
    pass


class TestFiling5:
    pass