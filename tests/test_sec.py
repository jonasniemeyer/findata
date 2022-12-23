import re
import requests
from finance_data.sec import _SECFiling
from finance_data.utils import HEADERS
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

NoneType = type(None)

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
        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", filing["accepted"])) == 1
        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", filing["date_filed"])) == 1
        assert isinstance(filing["file_number"], (str, NoneType))
        assert isinstance(filing["film_number"], (int, NoneType))
    
    filings = latest_sec_filings(start="2022-12-22", timestamps=True)
    for filing in filings:
        assert isinstance(filing["accepted"], int)
        assert isinstance(filing["date_filed"], int)


class TestSECFiling:
    @classmethod
    def setup_class(cls):
        file = requests.get(url="https://www.sec.gov/Archives/edgar/data/320193/000119312519041014/0001193125-19-041014.txt", headers=HEADERS).text
        cls.file = _SECFiling(file=file)
    
    def test_attributes(self):
        assert self.file.accession_number  == "0001193125-19-041014"
        assert self.file.date_filed == "2019-02-14"
        assert self.file.date_of_change == "2019-02-14"
        assert self.file.date_of_period is None
        assert isinstance(self.file.document, str)
        assert self.file.document_count == 1
        assert self.file.effectiveness_date is None
        assert isinstance(self.file.file, str)
        assert self.file.file_number == "005-33632"
        assert self.file.film_number == 19607502
        assert isinstance(self.file.header, str)
        assert self.file.is_amendment is False
        assert self.file.is_html is True
        assert self.file.is_xml is False
        assert self.file.submission_type == "SC 13G"

    def test_from_url(self):
        assert _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/320193/000119312519041014/0001193125-19-041014.txt")
    
    def test_date_of_period(self):
        file = _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/320193/000032019322000063/0000320193-22-000063.txt")
        assert file.date_of_period == "2022-05-06"
    
    def test_effectiveness_date(self):
        file = _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/1336528/000117266122002568/0001172661-22-002568.txt")
        assert file.effectiveness_date == "2022-11-14"

    def test_amendment(self):
        file = _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/102909/000093247118004625/0000932471-18-004625.txt")
        assert file.is_amendment is True

    def test_text_file(self):
        file = _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/315066/000031506610001412/0000315066-10-001412.txt")
        assert file.is_html is False

    def test_xml_file(self):
        file = _SECFiling.from_url("https://www.sec.gov/Archives/edgar/data/320193/000032019322000113/0000320193-22-000113.txt")
        assert file.is_xml is True


class TestFilingNPORT:
    @classmethod
    def setup_class(cls):
        cls.file = FilingNPORT.from_url("https://www.sec.gov/Archives/edgar/data/930667/000175272422234894/0001752724-22-234894.txt")

    def test_attributes(self):
        assert self.file.accession_number  == "0001752724-22-234894"
        assert self.file.date_filed == "2022-10-25"
        assert self.file.date_of_change == "2022-10-25"
        assert self.file.date_of_period == "2022-08-31"
        assert isinstance(self.file.document, str)
        assert self.file.document_count == 1
        assert self.file.effectiveness_date is None
        assert isinstance(self.file.file, str)
        assert self.file.file_number == "811-09102"
        assert self.file.film_number == 221328659
        assert isinstance(self.file.header, str)
        assert self.file.has_short_positions is False
        assert self.file.is_amendment is False
        assert self.file.is_html is False
        assert self.file.is_xml is True
        assert self.file.submission_type == "NPORT-P"

        filer = self.file.filer
        assert filer["name"] == "iShares, Inc."
        assert filer["cik"] == 930667
        assert filer["sic"]["name"] is None
        assert filer["sic"]["code"] is None
        assert filer["irs_number"] == 510396525
        assert filer["state"] == "MD"
        assert filer["fiscal_year_end"] == "2022-08-31"
        business_address = filer["business_address"]
        assert business_address["street1"] == "400 HOWARD STREET"
        assert business_address["street2"] is None
        assert business_address["city"] == "SAN FRANCISCO"
        assert business_address["state"] == "CA"
        assert business_address["zip"] == 94105
        assert business_address["phone"] == "(415) 670-2000"
        mail_address = filer["mail_address"]
        assert mail_address["street1"] == "400 HOWARD STREET"
        assert mail_address["street2"] is None
        assert mail_address["city"] == "SAN FRANCISCO"
        assert mail_address["state"] == "CA"
        assert mail_address["zip"] == 94105
        former_names = filer["former_names"]
        for item in former_names:
            assert isinstance(item["name"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", item["date_of_change"])) == 1

    def test_general_information(self):
        info = self.file.general_information
        assert info["filer_lei"] == "549300MGJZCNMJLBAJ67"
        assert info["series"]["name"] == "iShares MSCI World ETF"
        assert info["series"]["cik"] == "S000035395"
        assert info["series"]["lei"] == "549300SBOOZR51TG3W64"

        assert info["classes"][0]["cik"] == "C000108746"
        assert info["classes"][0]["name"] == "iShares MSCI World ETF"
        assert info["classes"][0]["ticker"] == "URTH"

        assert info["fiscal_year_end"] == "2022-08-31"
        assert info["reporting_date"] == "2022-08-31"
        assert info["is_final_filing"] is False

    def test_fund_information(self):
        info = self.file.fund_information
        assert info["total_assets"] == 2172722751.8
        assert info["total_liabilities"] == 46019387.76
        assert info["net_assets"] == 2126703364.04

        assets = info["certain_assets"]
        assert isinstance(assets["miscellaneous_securities"], float)
        assert isinstance(assets["assets_foreign_controlled_company"], float)
        payables = assets["accounts_payable"]
        for key in ("1-year", "long_term"):
            assert isinstance(payables[key]["banks"], float)
            assert isinstance(payables[key]["controlled_companies"], float)
            assert isinstance(payables[key]["other_affiliates"], float)
            assert isinstance(payables[key]["other"], float)
        assert isinstance(assets["liquiditation_preference"], float)
        assert isinstance(assets["cash"], float)

        assert info["portfolio_level_risk"] is None

        lending = info["securities_lending"]
        for borrower in lending["borrowers"]:
            assert isinstance(borrower["name"], str)
            assert isinstance(borrower["lei"], str)
            assert isinstance(borrower["value"], float)
        assert lending["non_cash_collateral"] is None

        returns = info["return_information"]
        for class_, data in returns["class_returns"].items():
            assert class_.startswith("C")
            for date, value in data.items():
                assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", date)) == 1
                assert isinstance(value, float)

        for derivative, data in returns["derivative_gains"].items():
            assert derivative in (
                "Commodity Contracts",
                "Credit Contracts",
                "Equity Contracts",
                "Foreign Exchange Contracts",
                "Interest Rate Contracts",
                "Other Contracts"
            )
            for key, value in data.items():
                if len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", key)) == 1:
                    if value is not None:
                        assert isinstance(value["realized_gain"], float)
                        assert isinstance(value["unrealized_appreciation"], float)
                else:
                    assert key in ("Forward", "Future", "Option", "Swap", "Swaption", "Warrant", "Other")
                    for date, instrument_value in value.items():
                        assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", date)) == 1
                        if instrument_value is not None:
                            assert isinstance(instrument_value["realized_gain"], float)
                            assert isinstance(instrument_value["unrealized_appreciation"], float)

        for date, data in returns["non-derivative_gains"].items():
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", date)) == 1
            assert isinstance(data["realized_gain"], float)
            assert isinstance(data["unrealized_appreciation"], float)

        for date, data in info["flow_information"].items():
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", date)) == 1
            assert isinstance(data["sales"], float)
            assert isinstance(data["reinvestments"], float)
            assert isinstance(data["redemptions"], float)

        assert info["liquid_investment_minimum_information"] is None
        assert info["derivatives_transactions"] is None
        assert info["derivatives_exposure"] is None
        assert info["var_information"] is None

    def test_portfolio(self):
        portfolio = self.file.portfolio()
        for var in (None, "name", "market_value", "quantity", "percentage", "payoff_direction"):
            self.file.portfolio(sorted_by=var)
        
        for item in portfolio:
            assert isinstance(item["issuer"]["name"], str)
            assert isinstance(item["issuer"]["lei"], (str, NoneType))
            assert isinstance(item["issuer"]["type"]["name"], str)
            assert isinstance(item["issuer"]["type"]["abbreviation"], str)
            assert isinstance(item["issuer"]["country"], str)

            assert isinstance(item["title"], str)

            for identifier, value in item["identifier"].items():
                assert isinstance(identifier, str)
                assert isinstance(value, str)

            assert isinstance(item["amount"]["percentage"], float)
            assert isinstance(item["amount"]["market_value"], float)
            assert isinstance(item["amount"]["quantity"], float)
            assert isinstance(item["amount"]["quantity_type"]["name"], str)
            assert isinstance(item["amount"]["quantity_type"]["abbreviation"], str)
            assert isinstance(item["amount"]["currency"]["name"], str)
            assert isinstance(item["amount"]["currency"]["exchange_rate"], (float, NoneType))

            assert item["payoff_direction"] in ("Long", "Short", None)

            assert isinstance(item["asset_type"]["name"], str)
            assert isinstance(item["asset_type"]["abbreviation"], str)

            assert isinstance(item["restricted_security"], bool)
            assert item["us_gaap_fair_value_hierarchy"] in (1, 2, 3)

            assert isinstance(item["securities_lending"]["cash_collateral"], (float, NoneType))
            assert isinstance(item["securities_lending"]["non_cash_collateral"], (float, NoneType))
            assert isinstance(item["securities_lending"]["loaned"], (float, NoneType))

    def test_miscellaneous_securities(self):
        pass

    def test_explanatory_notes(self):
        notes = self.file.explanatory_notes
        for section, note in notes.items():
            assert isinstance(section, str)
            assert isinstance(note, str)

    def test_signature(self):
        signature = self.file.signature
        assert signature["date"] == "2022-09-30"
        assert signature["name"] == "Ann Frechette"
        assert signature["title"] == "Assistant Treasurer"
        assert signature["company"] == "iShares, Inc."
        assert signature["signature"] == "Ann Frechette"

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