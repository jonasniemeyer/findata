from finance_data import YahooReader, DatasetError
import numpy as np
import pandas as pd
import datetime as dt
import pytest

class TestClassMethods:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader
    
    @pytest.mark.skip()
    def test_crumb(self):
        assert self.reader.crumb() == ""
    
    def test_currencies(self):
        currencies = self.reader.currencies()
        assert isinstance(currencies, list)
        assert len(currencies) == 165
        assert {
            "short_name": "USD",
            "long_name": "US Dollar",
            "symbol": "USD"
        } in currencies

class TestEquity:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("AAPL")
    
    def test_ticker(self):
        assert self.reader.ticker == "AAPL"
    
    def test_name(self):
        assert self.reader.name == "Apple Inc."
    
    def test_isin(self):
        assert self.reader.isin() == "US0378331005"
    
    def test_security_type(self):
        assert self.reader.security_type == "EQUITY"
    
    def test_profile(self):
        profile = self.reader.profile()
        assert len(profile) == 12
        assert profile["address1"] == "One Apple Park Way"
        assert profile["city"] == "Cupertino"
        assert profile["state"] == "CA"
        assert profile["zip"] == "95014"
        assert profile["country"] == "United States"
        assert profile["phone"] == "408 996 1010"
        assert profile["website"] == "https://www.apple.com"
        assert profile["industry"] == "Consumer Electronics"
        assert profile["sector"] == "Technology"
        assert isinstance(profile["employees"], int)
        assert profile["description"] == "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. It also sells various related services. In addition, the company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; AirPods Max, an over-ear wireless headphone; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, HomePod, and iPod touch. Further, it provides AppleCare support services; cloud services store services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. Additionally, the company offers various services, such as Apple Arcade, a game subscription service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was incorporated in 1977 and is headquartered in Cupertino, California."
        
        executives = profile["executives"]
        for item in executives:
            assert isinstance(item["name"], str)
            assert item["age"] is None or isinstance(item["age"], int)
            assert isinstance(item["position"], str)
            assert item["born"] is None or isinstance(item["born"], int)
            assert item["salary"] is None or round(item["salary"], 2) == item["salary"]
            assert isinstance(item["exercised_options"], int)
            assert isinstance(item["unexercised_options"], int)
    
    def test_analyst_recommendations(self):
        recommendations = self.reader.analyst_recommendations()
        for item in recommendations:
            assert dt.date.fromisoformat(item["date"])
            assert isinstance(item["company"], str)
            assert item["old"] is None or isinstance(item["old"], str)
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
                assert round(item["bid"], 2) == item["bid"]
                assert round(item["ask"], 2) == item["ask"]
                assert item["volume"] is None or isinstance(item["volume"], int)
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
            assert item["shares"] is None or isinstance(item["shares"], int)
            assert item["file"] is None or isinstance(item["file"], str)
            assert dt.date.fromisoformat(item["latest_trade"][0])
            assert isinstance(item["latest_trade"][1], str)
        
        insider = self.reader.insider_ownership(timestamps=True)
        for item in insider:
            assert item["date"] is None or isinstance(item["date"], int)
    
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
            assert item["file"] is None or isinstance(item["file"], str)
            assert item["text"] is None or isinstance(item["text"], str)
        
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

        key = list(income)[-1]
        total_variables = 0
        for item in (income, balance, cashflow):
            total_variables += len(item[key])
        assert len(statement_merged[key]) == total_variables - 1 #net income on income and cf statement have different names

        for date in income:
            for var in income[date]:
                assert income[date][var] is None or isinstance(income[date][var], (int, float))
        for date in balance:
            for var in balance[date]:
                assert balance[date][var] is None or isinstance(balance[date][var], (int, float))
        for date in cashflow:
            for var in cashflow[date]:
                assert cashflow[date][var] is None or isinstance(cashflow[date][var], (int, float))
        
        for type_ in ("income_statement", "balance_sheet", "cashflow_statement"):
            for date in statement[type_]:
                for var in statement[type_][date]:
                    assert statement[type_][date][var] is None or isinstance(statement[type_][date][var], (int, float))
        for date in statement_merged:
            for var in statement_merged[date]:
                assert statement_merged[date][var] is None or isinstance(statement_merged[date][var], (int, float))

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
        assert self.reader.logo() == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00L\\\xf6\x9c\x00\x00\x08\x8bIDATx\x9c\xec\x9cmH\x93_\x1f\xc7w\xae\xed\xcfr6g\xd3)\t&\x95\xd2\x83\x18i&)%\xe8\x10\xcd\xa0(\xed\x01\xc3\xac\xa4$)\x04\x15{\x13He/\xeaM/\n\xc2\nC)}\x13Df\x96(e\xf6\xa2\xe8M\xf4\xa0B\x94\xb5l\xad\x19\xf4\xc06Y\xba\x9ds\x83\xe7\xcf\xc5X\x9bv\xdf7^\xdf\xcb<\x9f\x172\xf7t~\xd7\xf9\\\xe7w\x1e\xae\xb3K\xc7\x18\xd3\x08pH\xe8\x00\xe6;B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x0e\x1d\xc0\xac ox\xe5\x0f$I\xbd\xe7\x99z#\xfb\x7f \x84\xb0)\xf8\xbfj\xde\x80\xfc\xf7\x08\xe0\xb5\xcc\xffRJ\xfd~\xff\xa3G\x8f\x1a\x1b\x1bKJJ^\xbcx\x81\x8e.,\x7fO\n\x92\x05x<\x9e\xabW\xaf^\xb9rett\x94\'\x9fc\xc7\x8e\xa1\xa3\x0b\xcb\xdf#\x80\x9f\xf8}}}uuu\xa3\xa3\xa3<\xf53\xc6t:]DD\x04:\xb4\xb0\xccy\x01\x81\x89\xfe\xfa\xf5\xeb555\x8c1B\x08\xa5\x941&IR\\\\\x9c\xc5bA\x87\x19\x96\xbf\xa7\x0f\xb8t\xe9Rmm\xad\x9c\x88\xc8\x14\x94\xd2\x94\x94\x94\xa4\xa4$tta\x99\xf3-\x80WwOO\xcf\xc9\x93\'}>_\xd0K\x92$\xe5\xe6\xe6\xeat\xea=\xcc9\xdf\x02\x18cccc\r\r\r\x13\x13\x13\xf2\x93|\x18\xca\x1f\x17\x14\x14\x88a\xe8,\xc2\x18;q\xe2\xc4\xc7\x8f\x1f\x83\x9e\xe4\x0e\n\x0b\x0b\xd3\xd2\xd2\x08!\xb8\x00g\x80\xa8\xf9\xec\xf8\x13FFF233\xfd~\xff\xef/EDD<~\xfc899\x99\xb7\tDt3\xa3\xde\xe4\xf8\x87\xdc\xb8q\x83R\x1a\xf2\xa5\xd3\xa7O\'\'\'\xab\xb6\xea9s>\x05\xf5\xf4\xf4\x84l\xc4\x95\x95\x95\x07\x0e\x1c@D\xf4\xdf1WS\x10\x0f\xdb\xeb\xf5&$$\xf8\xfd~y\xd0\xc9S\x7fuuuSS\x93$I\xfcyt\xb0\xd31WS\x10\xafh\xbb\xddN)\xe53^\xbf\xdf/I\xd2\xa2E\x8b\xce\x9d;WRR\xc2%\xa9y\x1d\x94\xa3R\x01|\x18\x13\xf8 $\xbc\xef\xa5\x94\xea\xf5\xfa\xac\xac\xac\xc2\xc2\xc2\x8a\x8a\x8a\x85\x0b\x17\xca\x1f\x91\x87C\xf2\xb7\xf1\xe7\xd5\xd3,\xd4\x98\x82\x02W\x92\xe5\xca\x92+1\xb0*].\xd7\xcd\x9b7\xf5z\xfd\x92%K\xd2\xd3\xd3\r\x06\x83<\x03 \x84x\xbd\xde\xef\xdf\xbf\xfb|>\x83\xc1`6\x9be\x13\xaaj\x19\xaa\x13\xc0\x18\x1b\x1f\x1f\xef\xed\xed\xbdw\xef\xde\xeb\xd7\xafm6\x9b\xc7\xe31\x99L)))\xd9\xd9\xd9EEE\xd9\xd9\xd9\xbc\x12y\xc6\x0f\xcc\xfe\x84\x10\x8f\xc7\xd3\xd7\xd7w\xff\xfe\xfd\'O\x9e|\xf8\xf0\x81?\xaf\xd1h\x0c\x06CjjjNN\xce\xd6\xad[\xd3\xd3\xd3\xb5Z-\xfa@\xff\x05/\x80W%_6p:\x9d\x17.\\hkks\xb9\\\xe1\x02KKK\xdb\xbbwoyyyddd\xe0\x97\xbcy\xf3\xa6\xbd\xbd\xbd\xa5\xa5\xc5\xe5r\x85+\x8b\xcbX\xbdzu]]\xdd\xb6m\xdbH\x00\xb3sp3\x83\x17\xc0\x97-)\xa5\xd7\xae];u\xea\x94\xdb\xed\x96G5!\xdf\xcf\x9f\x8f\x8a\x8a\xda\xb2eK~~\xbe\xc5by\xff\xfe}ww\xf7\x83\x07\x0f&\'\'y\x87\x1c\xae,\x9e\xdc\xb4Z-cl\xd7\xae]MMM\x16\x8be\xfe\n\x903\xf2\xf8\xf8xUUUWW\x17\xf7\xf1\x87\xd5\x11\x98\xd3\x83\xfa\xea\xc0\xb5\xa0p\xe5j4\x9a\xd4\xd4\xd4\xbbw\xefFGG\x03\x05 \xfb"\xc6\x98\xcf\xe7s\xbb\xdd\xf5\xf5\xf5\x9d\x9d\x9d\xbf\xd7\xe3\x8c\x1f\x97\xff\x06}j\xfa\xb3J~\xf3\xd0\xd0\xd0\x8e\x1d;\xdcn7\x9d\x02r.\xe2\x07\x03MMM\xed\xed\xed\x90a\tc\xec\xf9\xf3\xe7\xd5\xd5\xd5rKR>\x06\xb0\x80\xce\xce\xce\xe6\xe6f\xe0\xc6\x85\xa8\xa8\xa8\xf4\xf4t\xde\xeb@N\x02d\x1f\xe0t:\xf3\xf2\xf2\xecv;*\x00\xb3\xd9\xdc\xdc\xdcl\xb5Z\x81\xa3R\xccL\x98[oll\xb4\xdb\xed\xa8\xb6o\xb1XZZZ6m\xda\xa4|\xd1\x81\x00\x0e\x9ew\xb6\x9f>}\xe2m\x1fR\xfb\x8c\xb1\xcb\x97/\xef\xde\xbd\x1b\xbe&\x81\xe9\xfa\x08!\x1d\x1d\x1d>\x9f/\xdcR\xfel\x93\x93\x93SZZ\n\x9f\x03a\x04\xf0\x9cs\xfb\xf6m\xc8\xaeM\xae\xff\xcc\x993\xd2\x14\n\x97\xfe;\x98\x08\x1c\x0e\xc7\xe0\xe0 d\xf0C\x08\xb1Z\xadk\xd7\xaeU\xc9\x9eQ\x8c\x80g\xcf\x9eA\xca\xe5\x19\xbf\xac\xac\x8c\x9f\xfbj\x10\x80\x19\x05\xa1v\xcbRJ\r\x06CQQ\x91z\xae\x94a\xfa\x80\xa0]$J\x16\xbdb\xc5\nUm\x15\xc5\x8c\x82\x1c\x0e\x87\xf2\xe5r\x01\x89\x89\x89*9\xf79\x98>\xc0\xeb\xf5Bj\x81R\x1ax\x15A\r`R\x10j\xf6K\x08q\xbb\xddj\xe8{e0)h\xfa\xcb&\xb3\x07\xa5\xd4\xe9t*_\xee4`R\x90\xc9d\x82\x94+I\xd2\xf0\xf00j\xfa\x1d\x12\x8c\x80\xd8\xd8XT\x1e\xf0x</_\xbeT\xc9$\x00&`\xf9\xf2\xe5\xa8e\x00\xc6Xkkk\xc8\xcd\xbc\x100}@JJ\n\xaa\x13f\x8c\xdd\xbau\xeb\xcb\x97/A\xbb\x8fP`FA\x19\x19\x19\x90a(_\x89\xfb\xf9\xf3g}}=\xea"p\x10\x98<\x90\x98\x98\x18\x1f\x1f\x0f)\x9a\xd3\xd5\xd5\xd5\xdf\xdf\x0f\x0c@\x06#\x80\x10\x92\x93\x93\x03)\x9a\xa3\xd5j\xeb\xeb\xeb\x07\x07\x07\xe5D\x84j\r\xb0\xeb\x01yyy\xca\x17\x1d\xc8\xc8\xc8HEE\x85\xc3\xe1\xe0\xdb\xc2\xe4\rz\n\x03\xbb"QPP\x80\x9a\x8e\xc9\x9d\xc1\xbbw\xef\xf2\xf3\xf3\x07\x06\x06\x803\x03X\nJHHX\xb7n\x1dj]L\xde\x7f\xe7p8\xb6o\xdf~\xf4\xe8Q\x9b\xcd\x06\x89\x04&@\xa3\xd1\x1c:t\x08\xb5U?\xb0\xf1QJ;::\xce\x9f?\xaf|\x18\xe0\x8dY\x9b7o6\x9b\xcdj\x18\x0bj4\x9a\xd2\xd2R\xcc\xa9\xa0|\x912F\xa3\xf1\xc8\x91#\xc0\x00d2226n\xdc\x08)\x1a\xbc9\xf7\xe0\xc1\x83z\xbd\x1e\x18\x03\xa7\xaa\xaa\nU4X\x80\xd9l...F]\x1e\xe0,]\xba\xb4\xa4\xa4\x045\x1c@\n\xe0\xebq\xfb\xf6\xed\xe3\xbf\xedR>\x00.\xbe\xa1\xa1\xe1\x9f\x7f\xfeA]\xa6G\n\xe0\xa3\xef\xdc\xdc\xdc\x9d;wB\x02`\x8c\xadY\xb3\x06U:\x07\xff\x13%\xc6\xd8\xdb\xb7o\xb3\xb2\xb2\x94\x9f\rI\x92\xd4\xdd\xdd\xbda\xc3\x86y\xfa\x0b\x19\x99e\xcb\x96\x9d={V\xc9\x12y\xc2\xa9\xa8\xa8X\xbf~=\xf6\x14\xc4\x0b \x84h\xb5\xda\xfd\xfb\xf7\x17\x15\x15)V(c,--\xad\xa6\xa6\x86\xdf\xce@\xb1r\x7f\x07\x9f\x82d<\x1e\x8f\xd5j\x1d\x1e\x1eV\xa0,BHoooff&|\x8f\x10\xbe\x05\xc8DDD\xb4\xb6\xb6*s\xbd\xbe\xb6\xb66##C\x81\x82fDE-\x80_\xa7}\xf8\xf0aYY\xd9\xaf_\xbf\xa6yg\xd0\xbc!p\x9fK\xd0=!\x82\xe0\xef,..nkkS\xc9\x8d\xe4T$\x80\x8f\x82\x18cw\xee\xdc9|\xf8p8\x07r\xedGFF\xaeZ\xb5*>>^\xa7\xd3\xfd\xf8\xf1chh\xe8\xeb\xd7\xaf\xf2\xfd\x12C\x1e\x17c\xccj\xb5\xb6\xb7\xb7/X\xb0@-\xb7\xec`\xaa\x81\xdfo\x98\xff\xed\xef\xefOJJ\x8a\n\xc0h4\xf2\x07qqq\xe5\xe5\xe5\x03\x03\x03\x13\x13\x13\xf2\x85\x14\xfe\x93\xe3W\xaf^\xd5\xd4\xd4,^\xbc\xd88\x85\xc9d\x92?e4\x1a\xa3\xa3\xa3\x1b\x1a\x1a\xbc^//\x05}\xb8\xff\xa2"\x012~\xbf\xdf\xe7\xf3\r\r\rUVVFGG\xcb\x0eV\xae\\y\xfc\xf8q\x9b\xcd\xc6\x7fY\x16\x12J\xe9\xb7o\xdf.^\xbch\xb5ZM&\x13\xaf\xfa\x98\x98\x98={\xf6<}\xfaT\xd9\xe3\xf8#T\x94\x828\x81w\xc2e\x8c\xb9\\\xae\xcf\x9f?3\xc6bcc\x03o\x80\x1bn\xe5\x80\xff\xe2\x97\x7f\xc9\xe4\xe4\xe4\xd8\xd8\x18!$&&F\xaf\xd7\xc3\xef\xcb\x11\x12\xd5\t\x98\xf1&M\xff\xdb\x97\x84\xbc\xa3\x81\x1aP\xa3\x80y\x85\x8a\xe6\x01\xf3\x13!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\x8c\x10\x00F\x08\x00#\x04\x80\x11\x02\xc0\x08\x01`\x84\x000B\x00\x18!\x00\xcc\x7f\x02\x00\x00\xff\xff\x1c\xa5y\x1b\xf8\xf3\xdd2\x00\x00\x00\x00IEND\xaeB`\x82'


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
    
    def test_isin(self):
        assert self.reader.isin() is None
    
    def test_security_type(self):
        assert self.reader.security_type == "ETF"
    
    def test_profile(self):
        profile = self.reader.profile()
        assert isinstance(profile["phone"], str)
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
                "average_price/earnings",
                "average_price/book",
                "average_price/sales",
                "average_price/cashflow"
            ):
            assert round(holdings["equity_data"][key], 2) == holdings["equity_data"][key]
        assert all(
            key in (
                "average_maturity",
                "average_duration",
            )
            for key in holdings["bond_data"]
        )
        for key in (
            "bb",
            "aa",
            "aaa",
            "a",
            "other",
            "b",
            "bbb",
            "below_b",
            "us_government"
        ):
            assert round(holdings["bond_ratings"][key], 4) == holdings["bond_ratings"][key]
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
        assert isinstance(profile["description"], str)
    
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
            assert isinstance(profile[key], str)
    
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
                "average_price/earnings",
                "average_price/book",
                "average_price/sales",
                "average_price/cashflow"
            ):
            assert round(holdings["equity_data"][key], 2) == holdings["equity_data"][key]
        assert all(
            key in (
                "average_maturity",
                "average_duration",
            )
            for key in holdings["bond_data"]
        )
        for key in (
            "bb",
            "aa",
            "aaa",
            "a",
            "other",
            "b",
            "bbb",
            "below_b",
            "us_government"
        ):
            assert round(holdings["bond_ratings"][key], 4) == holdings["bond_ratings"][key]
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
        cls.reader = YahooReader("AAPL230317C00100000")

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