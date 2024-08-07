import re
from findata.sec import _SECFiling
from findata import (
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
import pandas as pd
from pandas.tseries.offsets import DateOffset

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
        assert isinstance(item["ticker"], (str, NoneType))
        assert isinstance(item["class_cik"], str)
        assert isinstance(item["series_cik"], str)
        assert isinstance(item["entity_cik"], int)


def test_latest_sec_filings():
    yesterday = (pd.to_datetime("today") - DateOffset(days=1)).date().isoformat()
    filings = latest_sec_filings(start=yesterday)
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
    
    filings = latest_sec_filings(start=yesterday, timestamps=True)
    for filing in filings:
        assert isinstance(filing["accepted"], int)
        assert isinstance(filing["date_filed"], int)


class TestSECFiling:
    @classmethod
    def setup_class(cls):
        cls.file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/320193/000119312519041014/0001193125-19-041014.txt")
    
    def test_attributes(self):
        assert self.file.accession_number  == "0001193125-19-041014"
        assert self.file.date_filed == "2019-02-14"
        assert self.file.date_of_change == "2019-02-14"
        assert self.file.date_of_period is None
        assert self.file.document_count == 1
        assert self.file.effectiveness_date is None
        assert self.file.file_number == "005-33632"
        assert self.file.film_number == 19607502
        assert self.file.is_amendment is False
        assert self.file.is_html is True
        assert self.file.is_xml is False
        assert self.file.submission_type == "SC 13G"
    
    def test_date_of_period(self):
        file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/320193/000032019322000063/0000320193-22-000063.txt")
        assert file.date_of_period == "2022-05-06"
    
    def test_effectiveness_date(self):
        file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/1336528/000117266122002568/0001172661-22-002568.txt")
        assert file.effectiveness_date == "2022-11-14"

    def test_amendment(self):
        file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/102909/000093247118004625/0000932471-18-004625.txt")
        assert file.is_amendment is True

    def test_text_file(self):
        file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/315066/000031506610001412/0000315066-10-001412.txt")
        assert file.is_html is False

    def test_xml_file(self):
        file = _SECFiling(url="https://www.sec.gov/Archives/edgar/data/320193/000032019322000113/0000320193-22-000113.txt")
        assert file.is_xml is True


class TestFilingNPORT:
    @classmethod
    def setup_class(cls):
        cls.file = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/930667/000175272422234894/0001752724-22-234894.txt")
        cls.derivative_file = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/1444822/000175272422264732/0001752724-22-264732.txt")

    def test_attributes(self):
        assert self.file.accession_number  == "0001752724-22-234894"
        assert self.file.date_filed == "2022-10-25"
        assert self.file.date_of_change == "2022-10-25"
        assert self.file.date_of_period == "2022-08-31"
        assert self.file.document_count == 1
        assert self.file.effectiveness_date is None
        assert self.file.file_number == "811-09102"
        assert self.file.film_number == 221328659
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
        assert filer["fiscal_year_end"] == {"day": 31, "month": 8}
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
                if key != "derivative_types":
                    assert value is None or isinstance(value["realized_gain"], float)
                    assert value is None or isinstance(value["unrealized_appreciation"], float)
            for key, deriv_data in data["derivative_types"].items():
                assert key in ("Forward", "Future", "Option", "Swap", "Swaption", "Warrant", "Other")
                for date, instrument_value in deriv_data.items():
                    assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", date)) == 1
                    assert instrument_value is None or isinstance(instrument_value["realized_gain"], (float))
                    assert instrument_value is None or isinstance(instrument_value["unrealized_appreciation"], float)

        for date, data in returns["non_derivative_gains"].items():
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

        security = portfolio[0]
        assert security["issuer"]["name"] == "Apple Inc"
        assert security["issuer"]["lei"] == "HWUPKR0MPOU8FGXBT394"
        assert security["issuer"]["type"]["name"] == "Corporate"
        assert security["issuer"]["type"]["abbr"] == "CORP"
        assert security["issuer"]["country"] == "US"
        assert security["title"] == "Apple Inc"
        assert security["identifier"]["cusip"] == "037833100"
        assert security["identifier"]["isin"] == "US0378331005"
        assert security["amount"]["percentage"] == 0.050511
        assert security["amount"]["market_value"] == 107420879.44
        assert security["amount"]["quantity"] == 683252.0
        assert security["amount"]["quantity_type"]["name"] == "Number of shares"
        assert security["amount"]["quantity_type"]["abbr"] == "NS"
        assert security["amount"]["currency"]["abbr"] == "USD"
        assert security["amount"]["currency"]["exchange_rate"] is None
        assert security["payoff_direction"] == "Long"
        assert security["asset_type"]["name"] == "Equity-common"
        assert security["asset_type"]["abbr"] == "EC"
        assert security["restricted_security"] is False
        assert security["liquidity_classification"] is None
        assert security["us_gaap_fair_value_hierarchy"] == 1
        assert security["debt_information"] is None
        assert security["repo_information"] is None
        assert security["derivative_information"] is None
        assert security["securities_lending"]["cash_collateral"] is None
        assert security["securities_lending"]["non_cash_collateral"] is None
        assert security["securities_lending"]["loaned"] is None

        for item in portfolio:
            assert isinstance(item["issuer"]["name"], str)
            assert isinstance(item["issuer"]["lei"], (str, NoneType))
            assert isinstance(item["issuer"]["type"]["name"], str)
            assert isinstance(item["issuer"]["type"]["abbr"], str)
            assert isinstance(item["issuer"]["country"], str)

            assert isinstance(item["title"], str)

            for identifier, value in item["identifier"].items():
                assert isinstance(identifier, str)
                assert isinstance(value, str)

            assert isinstance(item["amount"]["percentage"], float)
            assert isinstance(item["amount"]["market_value"], float)
            assert isinstance(item["amount"]["quantity"], float)
            assert isinstance(item["amount"]["quantity_type"]["name"], str)
            assert isinstance(item["amount"]["quantity_type"]["abbr"], str)
            assert isinstance(item["amount"]["currency"]["abbr"], str)
            assert isinstance(item["amount"]["currency"]["exchange_rate"], (float, NoneType))

            assert item["payoff_direction"] in ("Long", "Short", None)

            assert isinstance(item["asset_type"]["name"], str)
            assert isinstance(item["asset_type"]["abbr"], str)

            assert isinstance(item["restricted_security"], bool)
            assert item["us_gaap_fair_value_hierarchy"] in (1, 2, 3)

            assert isinstance(item["securities_lending"]["cash_collateral"], (float, NoneType))
            assert isinstance(item["securities_lending"]["non_cash_collateral"], (float, NoneType))
            assert isinstance(item["securities_lending"]["loaned"], (float, NoneType))

    def test_debt_security(self):
        portfolio = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/1100663/000175272422234846/0001752724-22-234846.txt").portfolio()
        portfolio = [security for security in portfolio if security["debt_information"] is not None]
        
        info = portfolio[0]["debt_information"]
        assert info["maturity"] == "2051-02-15"
        assert info["coupon"]["rate"] == 0.0188
        assert info["coupon"]["type"] == "Fixed"
        assert info["in_default"] is False
        assert info["coupon_payments_deferred"] is False
        assert info["paid_in_kind"] is False
        assert info["convertible_information"] is None
        
        for security in portfolio:
            info = security["debt_information"]
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", info["maturity"])) == 1
            assert isinstance(info["coupon"]["rate"], float)
            assert isinstance(info["coupon"]["type"], str)
            assert isinstance(info["in_default"], bool)
            assert isinstance(info["coupon_payments_deferred"], bool)
            assert isinstance(info["paid_in_kind"], bool)
            assert isinstance(info["convertible_information"], NoneType)

    def test_debt_convertible(self):
        portfolio = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/1100663/000175272422218333/0001752724-22-218333.txt").portfolio()
        portfolio = [security for security in portfolio if security["debt_information"] is not None]

        info = portfolio[0]["debt_information"]
        assert info["maturity"] == "2025-06-01"
        assert info["coupon"]["rate"] == 0.0038
        assert info["coupon"]["type"] == "Fixed"
        assert info["in_default"] is False
        assert info["coupon_payments_deferred"] is False
        assert info["paid_in_kind"] is False
        convertible_info = info["convertible_information"]
        assert convertible_info["mandatory_convertible"] is False
        assert convertible_info["contingent_convertible"] is True
        assert convertible_info["conversion_asset"]["name"] == "Palo Alto Networks Inc"
        assert convertible_info["conversion_asset"]["title"] == "Palo Alto Networks Inc"
        assert convertible_info["conversion_asset"]["currency"] == "USD"
        assert convertible_info["conversion_asset"]["identifier"]["cusip"] == "697435105"
        assert convertible_info["conversion_asset"]["identifier"]["isin"] == "US6974351057"
        assert convertible_info["conversion_information"]["ratio"] == 3.3602
        assert convertible_info["conversion_information"]["currency"] == "USD"
        assert convertible_info["delta"] is None
        
        for security in portfolio:
            info = security["debt_information"]
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", info["maturity"])) == 1
            assert isinstance(info["coupon"]["rate"], float)
            assert isinstance(info["coupon"]["type"], str)
            assert isinstance(info["in_default"], bool)
            assert isinstance(info["coupon_payments_deferred"], bool)
            assert isinstance(info["paid_in_kind"], bool)
            convertible_info = info["convertible_information"]
            assert isinstance(convertible_info["mandatory_convertible"], bool)
            assert isinstance(convertible_info["contingent_convertible"], bool)
            assert isinstance(convertible_info["conversion_asset"]["name"], str)
            assert isinstance(convertible_info["conversion_asset"]["title"], str)
            assert isinstance(convertible_info["conversion_asset"]["currency"], str)
            for identifier, value in convertible_info["conversion_asset"]["identifier"].items():
                assert isinstance(identifier, str)
                assert isinstance(value, str)
            assert isinstance(convertible_info["conversion_information"]["ratio"], float)
            assert isinstance(convertible_info["conversion_information"]["currency"], str)
            assert isinstance(convertible_info["delta"], NoneType)

    def test_derivative_currency_forward(self):
        portfolio = self.derivative_file.portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Forward"]
        info = portfolio[0]["derivative_information"]
        assert info["type"]["name"] == "Forward"
        assert info["type"]["abbr"] == "FWD"
        assert info["counterparties"][0]["name"] == "JP Morgan Chase Bank"
        assert info["counterparties"][0]["lei"] == "7H6GLXDRUGQFU57RNE97"
        assert info["purchased"]["amount"] == 2651403.32
        assert info["purchased"]["currency"] == "USD"
        assert info["sold"]["amount"] == 4350500.0
        assert info["sold"]["currency"] == "NZD"
        assert info["settlement_date"] == "2022-12-21"
        assert info["unrealized_appreciation"] == 215522.7

        for item in portfolio:
            info = item["derivative_information"]
            assert info["type"]["name"] == "Forward"
            assert info["type"]["abbr"] == "FWD"
            for counterparty in info["counterparties"]:
                assert isinstance(counterparty["name"], str)
                assert isinstance(counterparty["lei"], str)
            assert isinstance(info["purchased"]["amount"], float)
            assert isinstance(info["purchased"]["currency"], str)
            assert isinstance(info["sold"]["amount"], float)
            assert isinstance(info["sold"]["currency"], str)
            assert isinstance(info["unrealized_appreciation"], float)

    def test_derivative_future(self):
        portfolio = self.derivative_file.portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Future"]
        info = portfolio[0]["derivative_information"]
        assert info["type"]["name"] == "Future"
        assert info["type"]["abbr"] == "FUT"
        assert info["counterparties"][0]["name"] == "CME Clearing House"
        assert info["counterparties"][0]["lei"] == "LCZ7XYGSLJUHFXXNXD88"
        assert info["reference_asset"]["name"] == "S&P 500 E-Mini Index"
        assert info["reference_asset"]["title"] is None
        assert info["reference_asset"]["identifier"] == "US78378X1072"
        assert info["trade_direction"] == "Short"
        assert info["expiration_date"] == "2022-12-16"
        assert info["notional_amount"] == -19988325.0
        assert info["currency"] == "USD"
        assert info["unrealized_appreciation"] == 2149974.91

        for item in portfolio:
            info = item["derivative_information"]
            assert isinstance(info["type"]["name"], str)
            assert isinstance(info["type"]["abbr"], str)
            for counterparty in info["counterparties"]:
                assert isinstance(counterparty["name"], str)
                assert isinstance(counterparty["lei"], str)
            assert isinstance(info["reference_asset"]["name"], (str, NoneType))
            assert isinstance(info["reference_asset"]["title"], (str, NoneType))
            if isinstance(info["reference_asset"]["identifier"], dict):
                for identifier, value in info["reference_asset"]["identifier"].items():
                    assert isinstance(identifier, str)
                    assert isinstance(value, str)
            else:
                assert isinstance(info["reference_asset"]["identifier"], (str, NoneType))
            assert info["trade_direction"] in ("Long", "Short")
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", info["expiration_date"])) == 1
            assert isinstance(info["notional_amount"], float)
            assert isinstance(info["currency"], str)
            assert isinstance(info["unrealized_appreciation"], float)

    def test_derivative_option(self):
        portfolio = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/1432353/000175272422218231/0001752724-22-218231.txt").portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Option"]
        info = portfolio[0]["derivative_information"]
        assert info["type"]["name"] == "Option"
        assert info["type"]["abbr"] == "OPT"
        counterparty = info["counterparties"][0]
        assert counterparty["name"] == "NDX US 08/19/22 C11925"
        assert counterparty["lei"] is None
        assert info["option_type"] == "Call"
        assert info["trade_direction"] == "Written"
        reference = info["reference_asset"]
        assert reference["name"] == "Call Option 11925 Aug 2022 on NASDAQ 100 STOCK INDEX"
        assert reference["title"] is None
        assert reference["identifier"] is None
        assert info["amount"]["quantity"] == -599600.0
        assert info["amount"]["quantity_type"]["name"] == "Number of shares"
        assert info["amount"]["quantity_type"]["abbr"] == "NS"
        assert info["exercise_data"]["price"] == 925.0
        assert info["exercise_data"]["currency"] == "USD"
        assert info["expiration_date"] == "2022-08-22"
        assert info["delta"] is None
        assert info["unrealized_appreciation"] == -395183757.78

        for security in portfolio:
            info = security["derivative_information"]
            assert isinstance(info["type"]["name"], str)
            assert isinstance(info["type"]["abbr"], str)
            for counterparty in info["counterparties"]:
                assert isinstance(counterparty["name"], (str, NoneType))
                assert isinstance(counterparty["lei"], (str, NoneType))
            assert info["option_type"] in ("Call", "Put")
            assert info["trade_direction"] in ("Written", "Purchased")
            reference = info["reference_asset"]
            assert isinstance(reference["name"], (str, NoneType))
            assert isinstance(reference["title"], (str, NoneType))
            if reference["identifier"] is not None:
                for identifier, value in reference["identifier"].items():
                    assert isinstance(identifier, str)
                    assert isinstance(value, str)
            assert isinstance(info["amount"]["quantity"], float)
            assert isinstance(info["amount"]["quantity_type"]["name"], str)
            assert isinstance(info["amount"]["quantity_type"]["abbr"], str)
            assert isinstance(info["exercise_data"]["price"], float)
            assert isinstance(info["exercise_data"]["currency"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", info["expiration_date"])) == 1
            assert isinstance(info["delta"], NoneType)
            assert isinstance(info["unrealized_appreciation"], float)

    def test_derivative_other(self):
        portfolio = self.derivative_file.portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Other"]

    def test_derivative_swap(self):
        portfolio = self.derivative_file.portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Swap"]

    def test_derivative_swaption(self):
        portfolio = FilingNPORT(url="https://www.sec.gov/Archives/edgar/data/1810747/000175272422261043/0001752724-22-261043.txt").portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Swaption"]

    def test_derivative_warrant(self):
        portfolio = self.derivative_file.portfolio()
        portfolio = [security for security in portfolio if security["derivative_information"] is not None and security["derivative_information"]["type"]["name"] == "Warrant"]
        info = portfolio[0]["derivative_information"]
        assert info["type"]["name"] == "Warrant"
        assert info["type"]["abbr"] == "WAR"
        counterparty = info["counterparties"][0]
        assert counterparty["name"] == "Cenovus Energy, Inc."
        assert counterparty["lei"] == "549300F4XPHJ7NOSP309"
        assert info["option_type"] == "Call"
        assert info["trade_direction"] == "Written"
        reference = info["reference_asset"]
        assert reference["name"] == "Cenovus Energy, Inc."
        assert reference["title"] == "Cenovus Energy, Inc."
        assert reference["identifier"]["cusip"] == "15135U109"
        assert info["amount"]["quantity"] == 1.0
        assert info["amount"]["quantity_type"]["name"] == "Number of shares"
        assert info["amount"]["quantity_type"]["abbr"] == "NS"
        assert info["exercise_data"]["price"] == 6.54
        assert info["exercise_data"]["currency"] == "CAD"
        assert info["expiration_date"] == "2026-01-01"
        assert info["delta"] is None
        assert info["unrealized_appreciation"] == -7123.76

        for security in portfolio:
            info = security["derivative_information"]
            assert isinstance(info["type"]["name"], str)
            assert isinstance(info["type"]["abbr"], str)
            for counterparty in info["counterparties"]:
                assert isinstance(counterparty["name"], str)
                assert isinstance(counterparty["lei"], str)
            assert info["option_type"] in ("Call", "Put")
            assert info["trade_direction"] in ("Written", "Purchased")
            reference = info["reference_asset"]
            assert isinstance(reference["name"], str)
            assert isinstance(reference["title"], str)
            for identifier, value in reference["identifier"].items():
                assert isinstance(identifier, str)
                assert isinstance(value, str)
            assert isinstance(info["amount"]["quantity"], float)
            assert isinstance(info["amount"]["quantity_type"]["name"], str)
            assert isinstance(info["amount"]["quantity_type"]["abbr"], str)
            assert isinstance(info["exercise_data"]["price"], float)
            assert isinstance(info["exercise_data"]["currency"], str)
            assert len(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", info["expiration_date"])) == 1
            assert isinstance(info["delta"], NoneType)
            assert isinstance(info["unrealized_appreciation"], float)

    def test_miscellaneous_securities(self):
        pass

    def test_explanatory_notes(self):
        notes = self.file.explanatory_notes
        for section, note in notes.items():
            assert isinstance(section, str)
            assert isinstance(note, str)

    def test_exhibits(self):
        pass

    def test_signature(self):
        signature = self.file.signature
        assert signature["date"] == "2022-09-30"
        assert signature["name"] == "Ann Frechette"
        assert signature["title"] == "Assistant Treasurer"
        assert signature["company"] == "iShares, Inc."
        assert signature["signature"] == "Ann Frechette"