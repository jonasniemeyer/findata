import numpy as np
import pandas as pd
import datetime as dt
import pytest
from finance_data import YahooReader, DatasetError

NoneType = type(None)

class TestClassMethods:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader
    
    def test_currencies(self):
        currencies = self.reader.currencies()
        assert isinstance(currencies, list)
        assert len(currencies) == 165
        assert {
            "short_name": "USD",
            "long_name": "US Dollar",
            "symbol": "USD"
        } in currencies
    
    def test_get_ticker(self):
        assert self.reader.get_ticker("JP3633400001") == "7203.T"
    

class TestEquity:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("AAPL")
    
    def test_ticker(self):
        assert self.reader.ticker == "AAPL"
    
    def test_name(self):
        assert self.reader.name == "Apple Inc."
    
    def test_security_type(self):
        assert self.reader.security_type == "EQUITY"
    
    def test_profile(self):
        profile = self.reader.profile()
        assert len(profile) == 14
        assert profile["address1"] == "One Apple Park Way"
        assert profile["address2"] is None
        assert profile["address3"] is None
        assert profile["city"] == "Cupertino"
        assert profile["state"] == "CA"
        assert profile["zip"] == "95014"
        assert profile["country"] == "United States"
        assert profile["phone"] == "408 996 1010"
        assert profile["website"] == "https://www.apple.com"
        assert profile["industry"] == "Consumer Electronics"
        assert profile["sector"] == "Technology"
        assert isinstance(profile["employees"], int)
        assert profile["description"] == "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. In addition, the company offers various services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was incorporated in 1977 and is headquartered in Cupertino, California."
        
        executives = profile["executives"]
        for item in executives:
            assert isinstance(item["name"], str)
            assert isinstance(item["age"], (int, NoneType))
            assert isinstance(item["position"], str)
            assert isinstance(item["born"], (int, NoneType))
            assert item["salary"] is None or round(item["salary"], 2) == item["salary"]
            assert isinstance(item["exercised_options"], int)
            assert isinstance(item["unexercised_options"], int)
    
    def test_analyst_recommendations(self):
        recommendations = self.reader.analyst_recommendations()
        for item in recommendations:
            assert dt.date.fromisoformat(item["date"])
            assert isinstance(item["company"], str)
            assert isinstance(item["old"], (str, NoneType))
            assert isinstance(item["new"], str)
            assert isinstance(item["change"], str)
            if item["change"] == "main":
                assert item["old"] == item["new"]
        
        recommendations = self.reader.analyst_recommendations(timestamps=True)
        for item in recommendations:
            assert isinstance(item["date"], int)
    
    def test_recommendation_trend(self):
        recommendation_trend = self.reader.recommendation_trend()
        assert all(isinstance(recommendation_trend[key], dict) for key in("today", "-1month", "-2months", "-3months"))
        for key in recommendation_trend:
            assert isinstance(recommendation_trend[key]["count"], int)
            assert round(recommendation_trend[key]["average"], 2) == recommendation_trend[key]["average"]
            assert isinstance(recommendation_trend[key]["strong_buy"], int)
            assert isinstance(recommendation_trend[key]["buy"], int)
            assert isinstance(recommendation_trend[key]["hold"], int)
            assert isinstance(recommendation_trend[key]["sell"], int)
            assert isinstance(recommendation_trend[key]["strong_sell"], int)
        assert not any(value == np.NaN for value in recommendation_trend["-1month"].values())
    
    def test_options(self):
        options = self.reader.options()
        assert ("calls" in options) and ("puts" in options)
        for type_ in ("calls", "puts"):
            for item in options[type_]:
                assert dt.date.fromisoformat(item["maturity"])
                assert round(item["strike"], 2) == item["strike"]
                assert isinstance(item["symbol"], str)
                assert round(item["last_price"], 2) == item["last_price"]
                assert item["bid"] is None or round(item["bid"], 2) == item["bid"]
                assert item["ask"] is None or round(item["ask"], 2) == item["ask"]
                assert isinstance(item["volume"], (int, NoneType))
                assert round(item["implied_volatility"], 4) == item["implied_volatility"]
                assert isinstance(item["itm"], bool)
        
        options = self.reader.options(timestamps=True)
        for type_ in ("calls", "puts"):
            for item in options[type_]:
                assert isinstance(item["maturity"], int)
    
    def test_institutional_ownership(self):
        holders = self.reader.institutional_ownership()
        assert isinstance(holders, list)
        for item in holders:
            assert dt.date.fromisoformat(item["date"])
            assert isinstance(item["company"], str)
            assert round(item["percentage"], 4) == item["percentage"]
            assert isinstance(item["shares"], int)
            assert round(item["value"], 2) == item["value"]
        
        holders = self.reader.institutional_ownership(timestamps=True)
        for item in holders:
            assert isinstance(item["date"], int)
    
    def test_fund_ownership(self):
        funds = self.reader.fund_ownership()
        assert isinstance(funds, list)
        for item in funds:
            assert dt.date.fromisoformat(item["date"])
            assert isinstance(item["fund"], str)
            assert round(item["percentage"], 4) == item["percentage"]
            assert isinstance(item["shares"], int)
            assert round(item["value"], 2) == item["value"]
        
        funds = self.reader.fund_ownership(timestamps=True)
        for item in funds:
            assert isinstance(item["date"], int)
    
    def test_insider_ownership(self):
        insider = self.reader.insider_ownership()
        assert isinstance(insider, list)
        for item in insider:
            assert item["date"] is None or dt.date.fromisoformat(item["date"])
            assert isinstance(item["name"], str)
            assert isinstance(item["position"], str)
            assert isinstance(item["shares"], (int, NoneType))
            assert isinstance(item["file"], (str, NoneType))
            assert dt.date.fromisoformat(item["latest_trade"][0])
            assert isinstance(item["latest_trade"][1], str)
        
        insider = self.reader.insider_ownership(timestamps=True)
        for item in insider:
            assert isinstance(item["date"], (int, NoneType))
    
    def test_ownership_breakdown(self):
        breakdown = self.reader.ownership_breakdown()
        assert round(breakdown["insider_ownership"], 4) == breakdown["insider_ownership"]
        assert round(breakdown["institutions_ownership"], 4) == breakdown["institutions_ownership"]
        assert round(breakdown["institutions_ownership_float"], 4) == breakdown["institutions_ownership_float"]
        assert isinstance(breakdown["count_institutions"], int)
    
    def test_insider_trades(self):
        trades = self.reader.insider_trades()
        assert isinstance(trades, list)
        for item in trades:
            assert dt.date.fromisoformat(item["date"])
            assert isinstance(item["name"], str)
            assert isinstance(item["position"], str)
            assert isinstance(item["shares"], int)
            assert item["value"] is None or round(item["value"], 2) == item["value"]
            assert isinstance(item["file"], (str, NoneType))
            assert isinstance(item["text"], (str, NoneType))
        
        trades = self.reader.insider_trades(timestamps=True)
        for item in trades:
            assert isinstance(item["date"], int)

    def test_esg_scores(self):
        scores = self.reader.esg_scores()
        assert dt.date.fromisoformat(scores["date"])
        for key in ("environment", "social", "governance"):
            assert round(scores["scores"][key], 2) == scores["scores"][key]
        for key in (
            "adult",
            "alcoholic",
            "animal_testing",
            "catholic",
            "controversial_weapons",
            "small_arms",
            "fur_and_leather",
            "gambling",
            "gmo",
            "military_contract",
            "nuclear",
            "pesticides",
            "palm_oil",
            "coal",
            "tobacco"
        ):
            assert isinstance(scores["involvements"][key], bool)
        
        scores = self.reader.esg_scores(timestamps=True)
        assert isinstance(scores["date"], int)

    def test_sec_filings(self):
        filings = self.reader.sec_filings()
        assert isinstance(filings, list)
        for item in filings:
            assert dt.date.fromisoformat(item["date_filed"])
            assert dt.datetime.fromisoformat(item["datetime_filed"])
            assert isinstance(item["form_type"], str)
            assert isinstance(item["description"], str)
            assert isinstance(item["url"], str)
        
        filings = self.reader.sec_filings(timestamps=True)
        for item in filings:
            assert isinstance(item["date_filed"], int)
            assert isinstance(item["datetime_filed"], int)

    def test_financial_statement(self):
        income = self.reader.income_statement()
        balance = self.reader.balance_sheet()
        cashflow = self.reader.cashflow_statement()
        statement = self.reader.financial_statement()
        statement_merged = self.reader.financial_statement(merged=True)

        assert statement == {
            "income_statement": income,
            "balance_sheet": balance,
            "cashflow_statement": cashflow
        }
        
        assert income.keys() == cashflow.keys()
        assert cashflow.keys() == statement_merged.keys()

        year = list(income)[-1]
        total_variables = 0
        for item in (income, balance, cashflow):
            total_variables += len(item[year])
        assert len(statement_merged[year]) == total_variables - 1 #net income on income and cf statement have different names

        for date in income:
            for var in income[date]:
                assert isinstance(income[date][var], (int, float, NoneType))
        for date in balance:
            for var in balance[date]:
                assert isinstance(balance[date][var], (int, float, NoneType))
        for date in cashflow:
            for var in cashflow[date]:
                assert isinstance(cashflow[date][var], (int, float, NoneType))
        
        for type_ in ("income_statement", "balance_sheet", "cashflow_statement"):
            for date in statement[type_]:
                for var in statement[type_][date]:
                    assert isinstance(statement[type_][date][var], (int, float, NoneType))
        for date in statement_merged:
            for var in statement_merged[date]:
                assert isinstance(statement_merged[date][var], (int, float, NoneType))

        income = self.reader.income_statement(timestamps=True)
        for date in income:
            if date != "TTM":
                assert isinstance(date, int)
        balance = self.reader.balance_sheet(timestamps=True)
        for date in balance:
            assert isinstance(date, int)
        cashflow = self.reader.cashflow_statement(timestamps=True)
        for date in cashflow:
            if date != "TTM":
                assert isinstance(date, int)
        statement = self.reader.financial_statement(timestamps=True)
        for type_ in ("income_statement", "balance_sheet", "cashflow_statement"):
            for date in statement[type_]:
                if date != "TTM":
                    assert isinstance(date, int)
        statement_merged = self.reader.financial_statement(merged=True, timestamps=True)
        for date in statement_merged:
            if date != "TTM":
                assert isinstance(date, int)

    def test_fund_statistics(self):
        with pytest.raises(DatasetError) as exception:
            self.reader.fund_statistics()

    def test_holdings(self):
        with pytest.raises(DatasetError) as exception:
            self.reader.holdings()
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique is True

    def test_logo(self):
        assert self.reader.logo() == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00L\\\xf6\x9c\x00\x00\n\xb6IDATx\x9c\xec\x9d[L\x1bG\x17\xc7q\xec\x1a\x8c\xcd\xc5\x80/lJ\xb1[\x17\\q\x17\xb5LE)\x88r)\xa0\x8aV*\xa5j+\xd5P\xd16o\x89x\xe2%\x8a\x94\x87\x88\x87\xe4!R$\x1e\x10\xb9)Q\x94<D\x11\x84`D\x84b%$\x8a\xc1\xa0\x08\x19\x07\x0c\xe1"\x9c\x18\x10\x06c;\xc46\xebO\x1f\x96\xf8\xf8Bq<\xbb3\xde\x8b\xf9=&{\xce\x1c\xf6\xef\x99\xd9\x99=s\x96\x17\x08\x04b\x8e\xa0\x8ecT\x07\x10\xed\x1c\t@1<\xaa\x03\xa0\x92\xb5\xb55\xbb\xdd\xee\xf1x\xf2\xf2\xf2\xe2\xe2\xe2(\x89!\xba\x04\xf0z\xbdf\xb3y~~\xdej\xb5.--moo\x07\xff\xfd\xec\xd9\xb3G\x02\xa0\xc5\xeb\xf5>}\xfa\xb4\xb7\xb7wkk\x8b\xeaX\xfe\x0f\xf6\x0b\xe0\xf3\xf9\x06\x07\x07\x1f>|\xe8v\xbb\x0f\xbb\x86\xcb\xe5F6\xa8\xff\xc1r\x01,\x16\xcb\x95+W\x1c\x0eG\xe8\xcb\xa8\x1a\x7fX.\xc0\xf8\xf8xWWW8W\xf2\xf9|\xf4\xe1\xfc;\xec\x14\xc0\xef\xf7\x0f\x0e\x0e\xde\xbf\x7f?\x9c\x8b\xc5b\xf1G\x1f}\x84>\xa8\x7f\x87\x85\x02\xf8\xfd\xfe\x8b\x17/\xbe|\xf92\xcc\xeb?\xfb\xec3\xc4\x11\x85\x82\x85\x0b\xb1\xfe\xfe\xfe\xf0\xef~LLLFF\x06\xcap>\x00\xdb\x040\x18\x0cz\xbd\x1e\xc8\xa4\xb0\xb0\x10Y8\x1f\x86UC\xd0\x8b\x17/n\xdc\xb8\x01d\xa2R\xa9\xe4r9\xb2\x88>\x0c{z\x00\x8e\xe3\xbd\xbd\xbd\xa0V\x1a\x8d\x06M8\xe1\xc2\x12\x01\x02\x81\xc0\xf5\xeb\xd7\x17\x17\x17\x81\xacD"\xd1W_}\x85,\xa8\xb0`\x89\x00z\xbd~dd\x04\xd4J\xa3\xd1\xc4\xc6\xc6\xa2\x89(\\\xd8 \x80\xcb\xe5\n\xf3\x91\xff=\x8a\x8a\x8a\x10\x84\x03\x06\x1b\x04\x18\x1a\x1a\xf2z\xbd\xa0V\xf9\xf9\xf9YYYh"\x02\x80\xf1\x02\xe08n0\x18@\xad\x84B\xe1\x9f\x7f\xfe\xc9\xe1p\xd0\x04\x05\x00\xe3\x050\x18\x0c!\xb69\x0f\xa3\xb1\xb1\x91\xc2\r\xb8\xfd0[\x00\x1c\xc7\x07\x06\x06@\xad\n\n\n\xca\xcb\xcb\xd1D\x04\x0c\xb3\x05XZZ\xfa\xe0V\xf3{H\xa5R\x9dN\x87,"`\x98\xbd\x126\x1a\x8d@\xd7\xcb\xe5\xf2\xf6\xf6\xf6\xf8\xf8xd\x11\x01\xc3\xec\x1e`\xb1X\xc2\xbf\x98\xcb\xe5\xfe\xf3\xcf?\x89\x89\x89(#\x02\x86\xc1=\x00\xc7\xf1\xa5\xa5\xa50/\x16\x08\x04mmm\xe9\xe9\xe9\x88\x83\x02\x86\xc1\x028\x9d\xce0\xafT*\x95\xad\xad\xadR\xa9\x14qDD`\xb0\x00a.\xbe\x8a\x8a\x8aZ[[)|\xe9\x18\x1a\x06\x0b\xb0\xb3\xb3\x13\xfa\x82\xf8\xf8\xf8_\x7f\xfd\x95\xf2\xfd\xce\xd00X\x80\x10\xb9$\x99\x99\x99\x85\x85\x85\xa5\xa5\xa5III\x91\r\n\x18\x06\x0bp\xf0M\xbaD"\xc9\xcd\xcd-//\xa7\xe1d{\x18\x1cF\xa7\xa7\xbb\\.\x8f\xc7\xf3\xdf?\x83\xc3IHH\xa0\xc9\xee\x02\x10\x14\x08\xb0\xb3\xb3\xb3\xb9\xb9\xb9\xb6\xb6\xb6\xb1\xb1\xb1\xbd\xbd\x1d\x08\x04\xde\xbd{\'\x10\x08\x12\x13\x13SRRd2\x19\xa2\tsggguu\xd5f\xb3mlllnn:\x1c\x0e\xbf\xdf\x1f\xfc/\x0e\x87\x93\x98\x98(\x14\n\x93\x92\x92\xa4R\xa9L&KJJ\x8a\xccV]\xe4\x86 \xa7\xd3i6\x9b\x8dF\xe3\xd4\xd4T\x88\xf9\x93\xc7\xe3egg\xabT*\xadV\x9b\x9a\x9a\n\xa5]\x93\xc94111;;\x1b\xfe\xaeujj\xaaF\xa3\xf9\xfa\xeb\xaf%\x12\t\xf9\x18B\x80\xbc\x07\xb8\xdd\xee\xd1\xd1Q\x93\xc9\x04\xb4j\rr|\x97\xdc\xdc\xdc\x9c\x9c\x1c\x91H\x14\xbe\xa1\xc3\xe1\x98\x9b\x9b3\x9b\xcd\xd3\xd3\xd3+++\xa0\xed\xee\xc1\xe1p\xe4r\xb9F\xa3\xd1j\xb5iii\x84\xfd\x84j\x02\x9d\x00\xc1\xb7\xe4\x8f\x1e="\xb0]|\x10\xa5RY^^\xae\xd1hx\xbcC{m \x10\xb0X,z\xbd~jj\x8a|\x8b\xfb\xe1\xf1x\xf5\xf5\xf5\xd5\xd5\xd5\xd0\x87GT\x02\xac\xad\xaduuu\x85\xbfU\x10&\x02\x81\xa0l\x97\xf7\x96\xb58\x8eONN>x\xf0`nn\x0en\x8b\xfbIKK;q\xe2\xc4\xc7\x1f\x7f\x0c\xd1\'|\x01\xfc~\xff\xe3\xc7\x8f{{{].\x17\\\xcf\xfb\x11\x8b\xc5*\x95J\xa9T\xfa|>\xab\xd5:33\xb3w\xda\x02)\x02\x81\xa0\xae\xae\xae\xb2\xb2\x12V:)d\x01\\.\xd7\xf9\xf3\xe7m6\x1bD\x9f4\x04\xc3\xb0S\xa7NA\xd9X\x85\xb9\x1d\x8d\xe3xOO\x0f\xeb\xef~LL\x8c\xcdf\x03M\xc1;\x0ch=`ee\xe5\xea\xd5\xabV\xab\x15\x8a7FPXX\xf8\xdbo\xbf\x91\xec\x07p\x04p:\x9d\xa7O\x9f~\xfb\xf6-yW\xccB.\x97wtt\x90Y\x81\xc3\x19\x82\xee\xdc\xb9\x13\x85w?&&\xe6\xcd\x9b7CCCd<@\x10\xa0\xaf\xaf\xef\xf9\xf3\xe7\xe4\xfd0\x14\xbd^?33C\xd8\x9c\xac\x00\xc3\xc3\xc3\x04r\x92\xd9\x84H$:v\x8c\xf8m$\xb5\x17\xf4\xea\xd5\xab\xdb\xb7o\x93\xf1\xc0h\xf8|~iii}}=\x99y\x98\x94\x00w\xef\xde\xc5q\x9c\x8c\x07\xe6\x92\x92\x92r\xf2\xe4I\x99LF\xd2\x0f\xf1\xbe3??\x0ft\x14\x8bMp\xb9\xdc\xbf\xfe\xfa\x8b\xfc\xdd\'\xde\x03|>_OO\x0f\xf9\xe6\x99\x88J\xa5\xfa\xe3\x8f?`\xe5X\x10\x14\xc0d2\xd9\xedv(\x110\x0b\x0c\xc3\xda\xdb\xdb\xc9\xcc\xba\xefA\xd0\xd1\xf8\xf88\xac\x08\x98Ess3\xc4\xbbOP\x00\x87\xc3199\t1\x08\xa6\xf0\xd3O?\xa9\xd5j\xb8>\x89\x08044\xe4\xf3\xf9\xe0\xc6A\x7f***\xaa\xab\xab\xa1\xbb\x05\x16\x00\xc7q\xd0\x9cd\x16\x10\x17\x17\xf7\xe3\x8f?\xa2\xf0\x0c,\x80\xc9d\xda\xdc\xdcD\x11\n\x9d\xa9\xa8\xa8@\x94\xf3\x02,\x00\x81\xd3\xa0,\x00\xdd\x89\x1a0\x01\xfc~?\x81\xe4\x06\xa6\x93\x95\x95\x95\x92\x92\x82\xc89\x98\x00\xcb\xcb\xcb\x1fL\x89e\x1f(\xe6\xde=\xc0\x04\x80\x9e\xe5@\x7fD"Q~~>:\xff`\x02\xbc~\xfd\x1aY$4\x05u9\'0\x01\xc8d\x991\x14\xb8Y@\x07\x01\x13\x00J\x8e\x1b\xb3@\x94\x91\xb8\x07\x98\x00\xd1\xb6\x02\x10\n\x85\xe8\x9e\x7f\x82\x80\t\xb0\xbe\xbe\x8e,\x12:\x92\xb2\x0b\xd2&\x00\x04\xf0\xfb\xfd\xd1\xf6\xfe+~\x17\xa4M\x00\x08\x804\xd7\x93\x9epvA\xda\x04\xb3O\xca\xa3\xe6\xd8.h\x9b@\xea\x9d\xe9\xe0\xbb m\x02@\x80(\xdc\x84\x88\x00\x00\x02PX\xe3\x9d*\xde\xee\x82\xb4\x89\xa3!(\x14\x8e]\x906\x01 \x00m\xcb-\xa0\xc3\xe9t\xae\xae\xae"m\x02@\x00Z\xd59\x8a\x18\xa8\xd7\x9e`C\x90P(D\x16\tMYXX@\xea\x1fL\x00\xfa\xd7\xbe\x80\x8e\xd5jE\xfa$\n&@\x14\x8eB\x1e\x8f\x07\xe9\xd1W0\x01\xe8Vp-2\xf4\xf5\xf5\xa1s\x0e&\x00=\xab~\xa1fjj\n\xdd\xd1\xcf\xa3\x1e\x10\x16\x13\x13\x13\x88<\x83\t\x80\xbat\x08m1\x18\x0c\x88N\xe2\x83\t\x80a\x18\x8a \xe8\x8f\xc3\xe1@t\x18\x0bL\x80\xe4\xe4\xe4(\xdc\x11\n\xf2\xe4\xc9\x13\xb3\xd9\x0c\xdd-\x98\x00<\x1e\x8f\x0e5\xf7\xa9\xa2\xbb\xbb\x1b\xfa\xb1\x14\xe0\xcd\xb8\x9c\x9c\x1c\xb8\x110\x08\xb7\xdb}\xf3\xe6M\xb8>\x81\x05\xa0\xf6\xab[\x94c\xb1X\xba\xbb\xbb!N\xc8\xc0\x02H$\x92\xcc\xccLX\xcd3\x11\xa3\xd1\xd8\xd9\xd9\tK\x03"\xef\x03\xbe\xf8\xe2\x0b(m3\x17\x9b\xcdv\xed\xda5(\xae\x88\x08@\xf9\xb7\xb7\xe8\xc0\xd8\xd8Xgg\'\xf9\x93\xd2D\x04\x90\xefB\xb2a\x16077w\xe1\xc2\x85{\xf7\xee\x91qB\xf0\x95d\x94O\x03\xfb\xe9\xef\xef\xbft\xe9R\xf8\xb5\xf4\xdf\x83{\xe6\xcc\x19\x02f>\x9f/j\x8f\n\x1f\xc4n\xb7\x8f\x8c\x8cx<\x9e\xb8\xb88\xb1X\x0cdK\xf0\xa4|^^\x1e1C\xb6\xe2v\xbb\x07\x06\x06\xb6\xb6\xb6\x94J%\x90!\xc1!H \x10D\xf3\x8a\xec0\x8a\x8b\x8bAM\x88\xa7\xa5\xd4\xd6\xd6\x12\xb6e%2\x99\x8c\xc09z\xe2\x02dgg3\xa8L\x7f\x04\xa8\xae\xae&\xb0SI*1\xeb\xcb/\xbf$c\xce&\x12\x12\x12JJJ\x08\x18\x92\x12 77\x97\x8c9\x9b\xc8\xca\xca"V\xcc\x98\x94\x00\n\x85"\x9aw\xa7\xf7C\xf8SAdsC\x7f\xfe\xf9\xe7\x10\xf5\xe4\xa3\x84\xe0\xb7k\x88\xd9\x92\x15 ##\xe3\xdbo\xbf%\xe9\x84\xe9466\x12.\xa6\x0e!;\xba\xa6\xa6&\x9a;\x81X,&\xf0\xf8\xbf\x07\x04\x01D"\x11\xb1\x07\x00vPVVF\xe6\x18\x13\x9c\xf3\x01555P\xfc0\x0e>\x9f_QQA\xc6\x03\x1c\x01d2\x99V\xab\x85\xe2\x8aY\xd4\xd4\xd4\x90\xcc\x18\x87vB\xa6\xb9\xb99\xda^\x12\xa8T\xaa\xef\xbe\xfb\x8e\xa4\x13h\x02\x08\x85\xc2\xbf\xff\xfe\x1b\xf5\xa1N\xfa\xc0\xe7\xf3\xdb\xda\xda\xc8\x7fI\x06\xe6\xfd\xc20\xac\xa0\xa0\x00\xa2C:\xa3\xd1h\x92\x93\x93\xc9\xfb\x81\xfc\x83\xfd\xe1\x87\x1f\x98\xf8AGP\xe2\xe3\xe3\xeb\xea\xea\xa0\xb8\x82,\x80\\.\xd7\xe9tp}\xd2\x10\x9dN\x07+O\x19\xfe\x90]TT\xd4\xd4\xd4\x04\xdd-}hjj\x828\xd2"\x993\xab\xaa\xaa\xd8\x9a@\x97\x9f\x9f_UU\x05\xd1!\xaa\x87\x96\x86\x86\x06D\x9e\xa9\x05\xfa\xdf\x85J\x80O>\xf9\xa4\xa5\xa5\x85M\xb9\xec<\x1eO\xa7\xd3)\x14\n\xb8n\x11>\xb6\x97\x94\x94\x90\\\xa6\xd3\n\x9dN\x87"%\x10\xed\xba\xa9\xa1\xa1\x81\xccN!}(..&\xfc\xca%4h\x05\x10\n\x85\xcd\xcd\xcdLO\xa3S\xa9T\xbf\xfc\xf2\x0b"\xe7\x91\xf8\xa6\xbc\xd7\xeb=w\xee\x1cC?\xf2\x89aXGG\x07\xbaB%\x91\xd8\xba\xe1\xf3\xf9:\x9d\x8e\x89\x132\x86a:\x9d\x0ei\x99\x98H\xf4\x80 \x0b\x0b\x0b\xb7n\xdd"\x7f\xec_\xa1P|\xfa\xe9\xa7R\xa9\xf4\xf8\xf1\xe3iii\xb1\xb1\xb1\xc1\x8f\x99omm\xd9\xed\xf6\x95\x95\x95\x85\x85\x85\xc5\xc5E\xf2E~\xd5juKK\x0b\x94\r\x9f\x10DN\x80 \x97/_~\xf6\xec\x19\x01C\x0c\xc3\xbe\xf9\xe6\x1b\xadV\x1bf\xbd\n\x8f\xc73::j4\x1a\xa7\xa7\xa7\t4WVV\xf6\xfb\xef\xbf\x130\x04%\xd2\x02\x04\xbf\xf4\xaf\xd7\xeb\xc3\xac@\'\x10\x084\x1aMee%\xe1,<\xa7\xd3i\xd8%\xcc\xb2\xbf\\.\xb7\xb6\xb6\xf6\xfb\xef\xbf\x8f\xcc\xd6z\xa4\x05\x08\xe2t:\x87\x87\x87GGG\x0f\x0e\x14\x1c\x0e\x07\xc3\xb0\xf4\xf4\xf4\xcf?\xff\\\xadVK$\x12(\x93G \x10\xb0\xdb\xedf\xb3yvv\xd6n\xb7\xdbl\xb6\x83\xbf\x80\x84\x84\x04\xadV[UU\x05\x9abN\x06j\x04\xd8c}}}lllqq\xd1\xedv\'\'\'+\x14\x8a\x82\x82\x82\x08T%\xf2z\xbd\xf3\xf3\xf3\xcb\xcb\xcb\xc1r\xe4\xb1\xb1\xb1j\xb5:##\x03u\xbb\x07\xa1X\x80#\xa2\xe5\r"m9\x12\x80b\x8e\x04\xa0\x98#\x01(\xe6?\x01\x00\x00\xff\xff\xa9\xa6\x8d\xe1m\x0f@\x02\x00\x00\x00\x00IEND\xaeB`\x82'


def test_logo_clearbit():
    logo = YahooReader("VOW.DE").logo()
    assert isinstance(logo, bytes)

def test_logo_missing():
    assert YahooReader("ACU").logo() == b"\n"

class TestHistoricalData:
    def test_default(self):
        data = YahooReader("SPY").historical_data()
        info = data["information"]
        assert isinstance(info["type"], str)
        assert isinstance(info["currency"], str)
        assert isinstance(info["utc_offset"], int)
        assert isinstance(info["timezone"], str)
        assert isinstance(info["exchange_timezone"], str)
        assert isinstance(info["url"], str)
        
        df = data["data"]
        assert all(
            col in (
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
                "dividends",
                "splits",
                "simple_returns",
                "log_returns"
            )
            for col in df.columns
        )
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert all(df[col].dtype == "float64" for col in df.columns if col != "volume")
        assert df["volume"].dtype == "int64"
    
    def test_timestamps(self):
        df = YahooReader("SPY").historical_data(timestamps=True)["data"]
        assert all(
            isinstance(date, int)
            for date in df.index
        )
        with pytest.raises(TypeError) as exception:
            df.resample("M").last()

    def test_returns_off(self):
        df = YahooReader("SPY").historical_data(frequency="1mo", returns=False)["data"]
        assert ("simple_returns" not in df.columns) and ("log_returns" not in df.columns)
    
    def test_monthly_frequency(self):
        df = YahooReader("SPY").historical_data(frequency="1mo")["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert isinstance(df.resample("Y").last(), pd.DataFrame)

    def test_hourly_frequency(self):
        df = YahooReader("SPY").historical_data(frequency="60m")["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert isinstance(df.resample("d").last(), pd.DataFrame)

    def test_minute_frequency(self):
        df = YahooReader("SPY").historical_data(frequency="1m")["data"]
        assert all(isinstance(date, pd.Timestamp) for date in df.index)
        assert isinstance(df.resample("h").last(), pd.DataFrame)
  

class TestETF:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("SPY")
    
    def test_security_type(self):
        assert self.reader.security_type == "ETF"
    
    def test_profile(self):
        profile = self.reader.profile()
        assert isinstance(profile["phone"], (str, NoneType))
        assert isinstance(profile["description"], str)
    
    def test_fund_statistics(self):
        statistics = self.reader.fund_statistics()
        assert isinstance(statistics["company"], str)
        assert isinstance(statistics["type"], str)
        assert round(statistics["expense_ratio"], 4) == statistics["expense_ratio"]
        assert round(statistics["turnover"], 4) == statistics["turnover"]
        assert round(statistics["aum"], 2) == statistics["aum"]
        assert isinstance(statistics["style"], str)
        assert isinstance(statistics["style_url"], str)
    
    def test_holdings(self):
        holdings = self.reader.holdings()
        assert round(holdings["equity_share"], 4) == holdings["equity_share"]
        assert round(holdings["bond_share"], 4) == holdings["bond_share"]
        for item in holdings["holdings"]:
            assert isinstance(item["ticker"], str)
            assert isinstance(item["name"], str)
            assert round(item["percentage"], 4) == item["percentage"]
        for key in (
                "average_price_to_earnings",
                "average_price_to_book",
                "average_price_to_sales",
                "average_price_to_cashflow"
            ):
                assert holdings["equity_data"][key] is None or round(holdings["equity_data"][key], 2) == holdings["equity_data"][key]
        assert holdings["equity_data"]["average_price_to_earnings"] > 5 # sometimes yahoo switches between price/fundamental and fundamental/price
        assert all(
            key in (
                "average_maturity",
                "average_duration",
            )
            for key in holdings["bond_data"]
        )
        assert tuple(holdings["bond_ratings"].keys()) == ("us_government",)
        assert round(holdings["bond_ratings"]["us_government"], 4) == holdings["bond_ratings"]["us_government"]
        for key in (
            "consumer_cyclical",
            "basic_materials",
            "consumer_defensive",
            "technology",
            "communication_services",
            "financial_services",
            "utilities",
            "industrials",
            "energy",
            "healthcare",
            "real_estate"
        ):
            assert round(holdings["sector_weights"][key], 4) == holdings["sector_weights"][key]
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True
    
    def test_logo(self):
        assert self.reader.logo != b"\n"
    
    def test_missing_data(self):
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()

class TestFuture:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("GC=F")

    def test_security_type(self):
        assert self.reader.security_type == "FUTURE"
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True

    def test_missing_data(self):
        assert self.reader.profile() == {}
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        with pytest.raises(DatasetError):
            self.reader.fund_statistics()
        with pytest.raises(DatasetError):
            self.reader.holdings()
        assert self.reader.logo() == b"\n"


class TestCurrency:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("EURUSD=X")

    def test_security_type(self):
        assert self.reader.security_type == "CURRENCY"
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True

    def test_missing_data(self):
        assert self.reader.profile() == {}
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        with pytest.raises(DatasetError):
            self.reader.fund_statistics()
        with pytest.raises(DatasetError):
            self.reader.holdings()
        assert self.reader.logo() == b"\n"

class TestCrypto:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("BTC-USD")

    def test_security_type(self):
        assert self.reader.security_type == "CRYPTOCURRENCY"
    
    def test_profile(self):
        profile = self.reader.profile()
        assert isinstance(profile["name"], str)
        assert profile["description"] is None
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True
    
    def test_missing_data(self):
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        with pytest.raises(DatasetError):
            self.reader.fund_statistics()
        with pytest.raises(DatasetError):
            self.reader.holdings()
        assert self.reader.logo() == b"\n"

class TestIndex:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("^GSPC")

    def test_security_type(self):
        assert self.reader.security_type == "INDEX"
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True
    
    def test_missing_data(self):
        assert self.reader.profile() == {}
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        with pytest.raises(DatasetError):
            self.reader.fund_statistics()
        with pytest.raises(DatasetError):
            self.reader.holdings()
        assert self.reader.logo() == b"\n"


class TestMutualFund:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("TRRHX")

    def test_security_type(self):
        assert self.reader.security_type == "MUTUALFUND"
    
    def test_profile(self):
        profile = self.reader.profile()
        for key in (
            "address1",
            "address2",
            "address3",
            "phone",
            "description"
        ):
            assert isinstance(profile[key], (str, NoneType))
    
    def test_esg_scores(self):
        scores = self.reader.esg_scores()
        assert dt.date.fromisoformat(scores["date"])
        for key in (
            "environment",
            "social",
            "governance",
        ):
            assert round(scores["scores"][key], 2) == scores["scores"][key]
        assert len(scores["involvements"]) == 0

        scores = self.reader.esg_scores(timestamps=True)
        assert isinstance(scores["date"], int)
    
    def test_holdings(self):
        holdings = self.reader.holdings()
        assert round(holdings["equity_share"], 4) == holdings["equity_share"]
        assert round(holdings["bond_share"], 4) == holdings["bond_share"]
        for item in holdings["holdings"]:
            assert isinstance(item["ticker"], str)
            assert isinstance(item["name"], str)
            assert round(item["percentage"], 4) == item["percentage"]
        for key in (
                "average_price_to_earnings",
                "average_price_to_book",
                "average_price_to_sales",
                "average_price_to_cashflow"
            ):
                assert round(holdings["equity_data"][key], 2) == holdings["equity_data"][key]
        assert all(
            key in (
                "average_maturity",
                "average_duration",
            )
            for key in holdings["bond_data"]
        )
        assert tuple(holdings["bond_ratings"].keys()) == ("us_government",)
        assert round(holdings["bond_ratings"]["us_government"], 4) == holdings["bond_ratings"]["us_government"]
        for key in (
            "real_estate",
            "consumer_cyclical",
            "basic_materials",
            "consumer_defensive",
            "technology",
            "communication_services",
            "financial_services",
            "utilities",
            "industrials",
            "energy",
            "healthcare"
        ):
            assert round(holdings["sector_weights"][key], 4) == holdings["sector_weights"][key]
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            print(freq)
            df = self.reader.historical_data(frequency=freq)["data"]
            assert isinstance(df, pd.DataFrame)
            assert all(isinstance(date, pd.Timestamp) for date in df.index)
            assert df.index.is_unique == True
    
    def test_missing_data(self):
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        assert self.reader.logo() == b"\n"


class TestOption:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("AAPL240621C00060000")

    def test_security_type(self):
        assert self.reader.security_type == "OPTION"
    
    def test_historical_data(self):
        for freq in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
            assert self.reader.historical_data(frequency=freq) is None
    
    def test_missing_data(self):
        assert self.reader.profile() == {}
        with pytest.raises(DatasetError):
            self.reader.analyst_recommendations()
        with pytest.raises(DatasetError):
            self.reader.recommendation_trend()
        with pytest.raises(DatasetError):
            self.reader.institutional_ownership()
        with pytest.raises(DatasetError):
            self.reader.fund_ownership()
        with pytest.raises(DatasetError):
            self.reader.insider_ownership()
        with pytest.raises(DatasetError):
            self.reader.ownership_breakdown()
        with pytest.raises(DatasetError):
            self.reader.insider_trades()
        with pytest.raises(DatasetError):
            self.reader.esg_scores()
        with pytest.raises(DatasetError):
            self.reader.sec_filings()
        with pytest.raises(DatasetError):
            self.reader.income_statement()
        with pytest.raises(DatasetError):
            self.reader.balance_sheet()
        with pytest.raises(DatasetError):
            self.reader.cashflow_statement()
        with pytest.raises(DatasetError):
            self.reader.fund_statistics()
        with pytest.raises(DatasetError):
            self.reader.holdings()
        assert self.reader.logo() == b"\n"