from finance_data import YahooReader, DatasetError
import numpy as np
import pytest

class TestClassMethods:
    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader

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
        assert self.reader.isin == "US0378331005"
    
    def test_security_type(self):
        assert self.reader.security_type == "EQUITY"

    def test_analyst_recommendations(self):
        recommendations = self.reader.analyst_recommendations()
        assert all(
            all(key in item.keys() for key in ("date", "firm", "old", "new"))
            for item in recommendations
        )
    
    def test_recommendation_trend(self):
        recommendation_trend = self.reader.recommendation_trend()
        assert all (
            key in recommendation_trend.keys()
            for key in ("today", "-1month", "-2months", "-3months")
        )
        assert all (
            all(
                key in item
                for key in ("count", "average", "strong_buy", "buy", "hold", "sell", "strong_sell")
            )
            for item in recommendation_trend.values()
        )
        assert not any(
            value == np.NaN
            for value in recommendation_trend["-1month"].values()
        )
    
    def test_options(self):
        options = self.reader.options()
        assert ("calls" in options.keys()) and ("puts" in options.keys())
        assert all(
            all(
                key in item.keys() for key in (
                    "maturity",
                    "symbol",
                    "last_price",
                    "bid",
                    "ask",
                    "volume",
                    "implied_volatility",
                    "itm"
                )
            )
            for item in options["calls"]
        )

    def test_institutional_ownership(self):
        holders = self.reader.institutional_ownership()
        assert isinstance(holders, list)
        assert all(
            all(
                key in item.keys() for key in (
                    "date",
                    "company",
                    "percentage",
                    "shares",
                    "value"
                )
            )
            for item in holders
        )

    def test_fund_ownership(self):
        funds = self.reader.fund_ownership()
        assert isinstance(funds, list)
        assert all(
            all(
                key in item.keys() for key in (
                    "date",
                    "fund",
                    "percentage",
                    "shares",
                    "value"
                )
            )
            for item in funds
        )

    def test_insider_ownership(self):
        insider = self.reader.insider_ownership()
        assert isinstance(insider, list)
        assert all(
            all(
                key in item.keys() for key in (
                    "date",
                    "name",
                    "position",
                    "shares",
                    "file",
                    "latest_trade"
                )
            )
            for item in insider
        )
        assert isinstance(insider[0]["latest_trade"], tuple)

    def test_ownership_breakdown(self):
        breakdown = self.reader.ownership_breakdown()
        assert isinstance(breakdown, dict)
        assert all(
            key in breakdown.keys() for key in (
                "insider_ownership",
                "institutions_ownership",
                "institutions_ownership_float",
                "count_institutions"
            )
        )

    def test_insider_trades(self):
        trades = self.reader.insider_trades()
        assert isinstance(trades, list)
        assert all(
            all(
                key in item.keys() for key in (
                    "date",
                    "name",
                    "position",
                    "shares",
                    "value",
                    "file",
                    "text"
                )
            )
            for item in trades
        )
        #assert whether transaction is a buy or sell

    def test_esg_scores(self):
        scores = self.reader.esg_scores()
        assert isinstance(scores, dict)
        assert all(
            key in scores.keys() for key in (
                "month",
                "scores",
                "involvements",
            )
        )
        assert isinstance(scores["month"], tuple)
        assert all(
            key in scores["scores"].keys() for key in (
                "environment",
                "social",
                "governance"
            )
        )
        assert all(
            key in scores["involvements"].keys() for key in (
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
            )
        )

    def test_sec_filings(self):
        filings = self.reader.sec_filings()
        assert isinstance(filings, list)
        assert all(
            all(
                key in item.keys() for key in (
                    "date_filed",
                    "datetime_filed",
                    "form_type",
                    "description",
                    "url"
                )
            )
            for item in filings
        )

    def test_financial_statement(self):
        income = self.reader.income_statement()
        balance = self.reader.balance_sheet()
        cashflow = self.reader.cashflow_statement()
        statement = self.reader.financial_statement()
        statement_merged = self.reader.financial_statement(merged=True)

        assert isinstance(income, dict)
        assert isinstance(balance, dict)
        assert isinstance(cashflow, dict)

        assert statement == {
            "income_statement": income,
            "balance_sheet": balance,
            "cashflow_statement": cashflow
        }

        assert isinstance(statement_merged, dict)
        assert income.keys() == balance.keys()
        assert balance.keys() == cashflow.keys()
        assert cashflow.keys() == statement_merged.keys()

        key = list(income.keys())[0]
        total_variables = 0
        for item in (income, balance, cashflow):
            total_variables += len(item[key].keys())
        assert len(statement_merged[key]) == total_variables - 1 #net income on income and cf


    def test_fund_statistics(self):
        with pytest.raises(DatasetError) as exception:
            self.reader.fund_statistics()

    def test_holdings(self):
        with pytest.raises(DatasetError) as exception:
            self.reader.holdings()

    def test_logo(self):
        assert self.reader.logo() == b"""\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00L\\\xf6\x9c\x00\x00\t\xc9IDATx\x9c\xec\x9c]H\x15[\x1b\xc7\xf7\xcc\x9a5{\x8f\xdb}\xfc8\x87}\x8e;P\xa1\x12?*\xd2L\x02\x13-IC\xd1\x0b\xbd\xd8\x84\xd1\x07\x12\x91\xd2M\xd8M]Z \xddE\x92]\x18\x1at\x13\x9aT\xb0\x11\xf2\xca\xc8\xbc))Q\xb4(5(\xa5m)j\xb6\xb7{f\xd6\xbc\xe0\xf36l\xfaP\x0f\xc7\xe6\x19m\xfd.\x0e\x1ekZk\x9e\xff<\x1f\xf3\xac\xb5F2\x0c\xc3\xc1\xc1C\xc4\x9e\xc0\xef\x0e\x17\x00\x19.\x002\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\\\x00d$\xec\t\xac\'\xe6Fc\xc6\x98\xf0\x15c\x19Q\xb4\xe9\xa3\xb6\xa9\x04\x10\x04\x811&\x8a"!\xe4\xfd\xfb\xf7\x81@`ll\xcc\xe7\xf3\xd5\xd7\xd7cO\xed\xe7\x18\x9b\x08]\xd7\r\xc3x\xf6\xecYII\x89\xa2(111\x8a\xa2\xf8\xfd~\xf8\xbd=\xd9\xf0\x1e\xc0\x18\x83g\xdf0\x8c\x85\x85\x85s\xe7\xce\xdd\xbe}\x9bR\xeat:5M#\x84\xb8\xddn\xdb\xc6\x9fM\x15\x82\xde\xbd{W[[\xfb\xe4\xc9\x13EQ\x18c\x9a\xa69\x1c\x0e]\xd7SSS\xb1\xa7\xb6\x12\x9bA\x00A\x104M\xab\xae\xae~\xf9\xf2%\xa5T\xd7uH\xbf\x84\x90P(\x94\x95\x95\x85=\xc1\x95\xb0\xafo\xae\x1dM\xd3\x8e\x1e=:::\nQU\x10\x04Q\x14!!SJ\x0b\x0b\x0b!L\xd9\x93\xcd\xe0\x01\xad\xad\xad\x81@\x00\x02=T\xa2f\x8a+//OLL\xc4\x9e\xe0J\x08\x1b\xfd\x90^0\x18LNN\xa6\x94\x8a\xa2hZ\x1f~6\x0cchh(99\x19\xc2\x14\xf6L\x7f\xcc\x06\xf6\x00\x886MMMd\x193\xce\x80\xf5#\x91HsssJJ\n\xf64Wa\xa3z\x00\x98[\xd7u\x9f\xcf\x17\x89D\xcc\xe8\x0f\xc2h\x9a\xe6\xf7\xfb\xdb\xdb\xdb\xb1\xa7\xb9:\x1b5\t\x83\xad\xfb\xfa\xfa\xe6\xe6\xe6\xcc\xe0\x03\xd6g\x8c\xed\xdf\xbf\xff\xc6\x8d\x1bv\xce\xbd&\x1bU\x00x\xde\x07\x06\x06\x08!\x9a\xa6A\xd9#\x8ab$\x12\xd9\xb7o\xdf\xbd{\xf7(\xa5\x1b\xc2\xb97\x80\x00?\xb3\xa3 \x08SSS\xe0\n\xa2(\xea\xba\xae\xaa\xea\xc5\x8b\x17\xbb\xbb\xbbcbb\xc4e\xec\xaf\xc1\x06H\xc2?+`\x18c\x7f\xff\xfd7\xa5\xd4\xe3\xf1x\xbd\xde\xc3\x87\x0f\xfb\xfd\xfe]\xbbv\x81\xd1\xcd\xc6\x9c\xe9.\x96O|M\xd87\t\xeb\xba\xfe\xf1\xe3\xc7\xe9\xe9iM\xd3<\x1e\x8f\xcf\xe7S\x14\x05\xfe\xc8,7gff\xde\xbcy\x03\x02\xfc\xf5\xd7_\x90\x8a\xc1\xe8\x8c\xb1`08;;\xab\xaa\xaa\xcb\xe5\xf2z\xbd\xf1\xf1\xf1\xd8\xf7\xf4#,o\xff\xfd\x00\xc6\x98\xaa\xaa\xd0\xb3TU\xb5\xa7\xa7\xa7\xae\xaen\xcb\x96-\x94RB\x88$I\x94R\xb7\xdb]RR\xd2\xda\xda:;;\x0b\x97@\xb5\xa3\xeb:cL_\xc60\x8c\x91\x91\x91k\xd7\xaeUTT$%%Ay\xeat:\t!\x94\xd2\x8c\x8c\x8c\x86\x86\x86\xbe\xbe>\xb8\x16.\xc4\xbeu\xc3.\x02\x80\xf9\xba\xba\xba\xb6m\xdb&\xcbrLLL\\\\\x9cg\x99\x84\x84\x04\x8f\xc7\xf3\xc7\x1f\x7f\xc4\xc7\xc7+\x8a\x92\x94\x94\xd4\xd0\xd0\x10\x0c\x06\xe1*0\xe2\xc2\xc2Bsss~~>\xb4?\xddnw\xdcW\xe0Z\xb8<66\x96\x10\x92\x9b\x9b\xfb\xf8\xf1c\x9bh`\x8b\x10d\x18\xc6\xa7O\x9f\xce\x9c9\xf3\xe0\xc1\x03\x97\xcb\x05!\x1bV\xb5\xa2#8\x84\x17\xe8t\x12B\x8a\x8b\x8b\x0b\n\n\x0c\xc3\xe8\xeb\xeb\xeb\xed\xed\r\x87\xc3.\x97\xcb,=\xe1\x07\xb3\x11\r\xf9\x00\xc4\x96e\xf9\xf3\xe7\xcfW\xae\\\xa9\xab\xab\xa3\x94\xe2\xbe\'#\x0b\x00\x16\x19\x1b\x1b;x\xf0\xe0\xfc\xfc<\xd8}\xe5K\xa0\xf5\x0fe\x0f4>\t!\xf0\xcbU\xc7\x8a\x16RU\xd5\xe3\xc7\x8f_\xbf~\xddl]\xa0(\x81Y\x86B\x10\x18\x1f\x1f\xf7\xfb\xfd\xf3\xf3\xf3\x10\x10\xd6r\x15\xa4h0=!d\x85R5\x1a\xd3\xb8\xa0\x16\xa5\xb4\xbd\xbd\xbd\xa5\xa5\x05\xfe\x17\xcb\t\x90=\x801VPP\xf0\xe2\xc5\x0bQ\x14%IRUu\x8d\x86\xf8\xef&3\x0cC\x96\xe5/_\xbe\xf4\xf6\xf6\xe6\xe5\xe5\xfd^\x1e\x00\x91\xc7\xe1p\x9c={vpp\x10b\x88\xa6ik\xbf\xff\xffb)\xf3\x917\x0c\xe3\xf2\xe5\xcb;v\xec\x80_\xa28\x01\x82\x07\x98#>\x7f\xfe\xbc\xa0\xa0\x80\x10b\xe5\x1c\x04A\xd0u\x1dJ\xdb\xa6\xa6\xa6\x93\'Ob\x99\xfe\xff\xf3A\x11\x00\x1e\xc0\x9c\x9c\x9c\x89\x89\x89\x7f\xf5\xe0\xaf\x0b\xa2(\x86\xc3\xe1\xbbw\xef\x96\x96\x96:\x1c\x0eI\xc2l\x07\xa0\x8d\xdd\xd3\xd3322\x02\xafZ\x90Q-\x1bZ\xd3\xb4\xfa\xfa\xfa\xf2\xf2r;\xb4(\x10<\x00\n\xfc\xea\xea\xea\x87\x0f\x1fZ\xbfa\xc40\x8c?\xff\xfcshh\xc8\xedv\xa3[\x1f\'\tC\xb1\xff\xe8\xd1#\xeb\x87v8\x1c\xaa\xaa666*\x8ab\x07\xeb\xa3\x95\xa1\x83\x83\x83{\xf6\xec1\x9bkV\xe2\xf5zGGG\xa1Ym\xfd\xe8\xdf\x833\x89\xfe\xfe~I\x92\xac4\x81\xd9"=r\xe4\x88\xc5u\xd7\xca\xe0\x08000 I\x92\x95K\x86\x90o#\x91Hee\xa5}\xac\x8f&\xc0\xdb\xb7o-~\xed\x84\xdaW\xd7u\xd8\xa5b\x93\xf8\x83&\xc0\xcc\xcc\x8c\xc59\x10<@\x96\xe5\xb8\xb88\x9b\xa4_\x00G\x00(\xfc\xad\x0c\x05\xe6\x91\r\xcbF\\#h\x9ehq \x96$\tr@8\x1c\xe69\xc0\x01\xcb \x16\x03ngn\xa4\xb0\t8\x02$&&\x9a\x0b^\xd6\x00O=!\xe4\xe9\xd3\xa7\xd6\xfb\xdf\n\xe0\x08\x90\x9a\x9a\n\x8b\x8bV\x0e\n\x8b0\x81@\xc0V\xc9\x00G\x80\xb4\xb4\xb4\xb5\xaf\xbd\xac\x17\xb0u\xee\xfe\xfd\xfb\xc3\xc3\xc3p~\xc6\x0e\xe0\x08\x90\x9d\x9d\x8d\xb5q\x93\x10r\xe9\xd2%X\xc8\xb4\x03\x08\x020\xc6\xf6\xee\xdd\x8b\x92\x87a\x19\xb2\xb3\xb3\xb3\xad\xad\xcd\xfa\xd1\x7f\x08\xda\x9apzz\xfa\xe4\xe4$\xca\xd0\xb0o\xb7\xbf\xbf\x7f\xfb\xf6\xed\xd1a\x10%1\xa0\xbd\x07\x14\x17\x17\xeb\xban\xfd\xb8\x92$\x85\xc3a\xc6XMM\xcd\xf8\xf8\xb8\xf9\xfcY\xfcbh\x82 \x00\xb4eJKKQ\x04\x88D"\x94R\xc6\xd8\xe8\xe8hUU\xd5\xc4\xc4D\xf42\xbd\xf5\xf3A[\x13\x0e\x87\xc3III\xd6\x97\xe4\xd1O:\xd4E7o\xde\xac\xaa\xaa\xfa\x8d\xb6\xa5\xc0M*\x8aRVV\x06N`\xfd\x1b\x99\t\x1cf\xca\xcf\xcf\x87}v\x96M\xc3\x04-\x049\x1c\x8e\xf3\xe7\xcf[\xbf%\xe2\x9b\x99\x08\x82\x00\x9b\xd7\t!(=j\x9c$\x0cq`\xf7\xee\xdd\x19\x19\x19\xe6FZ\x14\x08!\xe1p\xf8\xc4\x89\x13X\xd5 N\x08\x12\xbf\xd2\xd0\xd0\xb0\xb4\xb4\x84\xf2Z\x04\x0f\xc1\xd2\xd2\xd2\xce\x9d;+++\xb1\xcaP\xcc\xbd\xa1p\xc2"++\xeb\xc3\x87\x0f(\xb5\x00l\xb1\xbes\xe7Nii)<\x04\xbfE\x126\x11\x04\x81Rz\xec\xd81UU\xad\xaf\x02a\xb8\x94\x94\x94\xb2\xb22\xc4\xfe(\xf2\xf6t\xc6Xmm\xed\xd6\xad[\xe1\xb4\xa9\x95\xb1H\x10\x84\xa5\xa5\xa5\xa6\xa6&x;\x83\x83\xae\x96\x8dn\x82\xec\x01\x0e\x87\xe3\x9f\x7f\xfe\xa9\xab\xab\x0b\x85BN\xa7SUU\xcbF\xd7u=\'\'\xa7\xa2\xa2\x02\xb75\x8d\x7f>\x002Ann\xee\xc4\xc4\x845\xb6\x80Q$I\xea\xe8\xe8(,,\xc4\xed\x8c"\xef\xce\x80\x0f\xec9\x9d\xce\xce\xceN\x8f\xc7\x03\xa6\xf9\xa5m\x19\xc30\x08!\xaa\xaa^\xb8p\xe1\xc0\x81\x03\xe8\xabcv\xd9\x1e\x93\x96\x96v\xf5\xeaUUU\xe1\xbb\'\xbf\xee\xa9\x84\xca\'33\xf3\xd4\xa9S\x90\xf9qC\x90]\x040\x0c\xa3\xba\xba\xba\xb1\xb1qaa\x016\xac\xff\xa2Q\xe0\xe5\x0b\x1c\xce\x8c\x81\xbfb\xac5b\x8bc\xaa\xd1\xd4\xd4\xd4tuu\xc9\xb2\x1c}L5\xfakX@\xf4\x97\x08\xccS\xa8fe\x05?G\x872\xf8\xd7$I\n\x85B\x81@\xa0\xa8\xa8\xc8\xdc\x1f\x87\xeb\x01\xb6\xfbV\xc4\xad[\xb7B\xa1Pww\xb7,\xcb`\xb8\xe8\x8f1A\x04\xd7u=\x1c\x0e\x8b\xa2\x98\x98\x98\x18\x1b\x1b\x1b\x89D\x16\x17\x17\xe7\xe7\xe7EQ\x94e\xf9\xfb\xbd\xb7\x10g(\xa5sss---EEE\x86a\xe0\x1e\x8c1\xb1K\x08\x8a\xa6\xa3\xa3\xe3\xf4\xe9\xd3`b\xd3\xfap(\x15N\xc7\x1f:t\xa8\xbb\xbb;\x18\x0cNNN\xbez\xf5j||<\x18\x0c\x0e\x0f\x0f\xc3\xc6\x7fM\xd3\xcc\xe0n~\xbd\x18N\x02wvv\xd6\xd6\xd6\x9a\xa7\xd4\xb1ot\x19k\x0f\xe6\xaf\x8e\xaa\xaa\x9a\xa61\xc6\xda\xda\xda\xd2\xd3\xd3%IR\x14\xc5\xe5rQJ\x13\x12\x12\xfc~\xff\xc8\xc8\x08\x04\xee\xe8\xff\x9a\x9f\xcd]\\\\lii\xc9\xce\xce\x86o\xb7\xba\\.Y\x96\x9dNgyy\xf9\xeb\xd7\xaf\xd92\x91H\xc4>\xdf\xd2\xb5]\x0e0\x81\xf9=[\x86\x10\x92\x99\x99\x99\x9b\x9b\x0bqi\xd5\xa8\xcd\x18\x9b\x9e\x9e\xee\xef\xef\x9f\x9a\x9a\xf2z\xbdyyy>\x9f\xcf\xec\x03Zu\x07k\xc2\xbe\x02|\x93\x84\xe1\x197\x1b\x06+h\x00\xcaE\xff\x9d\xe8%0\xfbl\xc9\x02\xec+\x00\x10m\xca\xe8\xdd\x8c\xab\xda\xd1T\xeb\xfb\x84\xfc+\xe7\xfb\xaf\xb1\xbb\x00\xdf`\x87\x83\xa5\xeb\x8b\xbd\x02\xe2\xaal2\xebo<\x016\x1f\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x99u\xe8\x89o\xacwi\xebY\xf9\xe5\x91{\x002\xeb\xe0\x01\x9b\xaf=`%\xdc\x03\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\\\x00d\xb8\x00\xc8p\x01\x90\xe1\x02 \xc3\x05@\x86\x0b\x80\x0c\x17\x00\x19.\x002\xff\x0b\x00\x00\xff\xff\xdb\xa4\xdc\xcf^\xdeV\xe2\x00\x00\x00\x00IEND\xaeB`\x82"""

    def test_profile(self):
        profile = self.reader.profile()
        assert all(
            entry in profile.keys() for entry in [
                "address1",
                "city",
                "state",
                "zip",
                "country",
                "phone",
                "website",
                "industry",
                "sector",
                "employees",
                "description",
                "executives"
            ]
        )
        assert len(profile.keys()) == 12
        assert profile["address1"] == "One Apple Park Way"
        assert profile["city"] == "Cupertino"
        assert profile["state"] == "CA"
        assert profile["zip"] == "95014"
        assert profile["country"] == "United States"
        assert profile["phone"] == "408 996 1010"
        assert profile["website"] == "https://www.apple.com"
        assert profile["industry"] == "Consumer Electronics"
        assert profile["sector"] == "Technology"
        assert profile["employees"] == 154000
        assert profile["description"] == "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. It also sells various related services. In addition, the company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; AirPods Max, an over-ear wireless headphone; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, HomePod, and iPod touch. Further, it provides AppleCare support services; cloud services store services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. Additionally, the company offers various services, such as Apple Arcade, a game subscription service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was incorporated in 1977 and is headquartered in Cupertino, California."

        executives = profile["executives"]
        assert all(
            all(key in item.keys() for key in (
                "name",
                "age",
                "position",
                "born",
                "salary",
                "exersized_options",
                "unexersized_options"
            )
                )
            for item in executives
        )
        assert {
            "name": "Mr. Timothy D. Cook",
            "age": 59,
            "position": "CEO & Director",
            "born": 1961,
            "salary": 14769259,
            "exersized_options": 0,
            "unexersized_options": 0
        } in executives

def test_logo_clearbit():
    return
    #assert YahooReader("ESCA").logo() == 

def test_logo_missing():
    return

def test_historical_data():
    return


class TestETF:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("SPY")

    def test_security_type(self):
        assert self.reader.security_type == "ETF"

class TestFuture:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("GC=F")

    def test_security_type(self):
        assert self.reader.security_type == "FUTURE"

class TestCurrency:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("EURUSD=X")

    def test_security_type(self):
        assert self.reader.security_type == "CURRENCY"

class TestCrypto:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("BTC-USD")

    def test_security_type(self):
        assert self.reader.security_type == "CRYPTOCURRENCY"

class TestIndex:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("^SPX")

    def test_security_type(self):
        assert self.reader.security_type == "INDEX"

class TestFund:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("TRRHX")

    def test_security_type(self):
        assert self.reader.security_type == "MUTUALFUND"

class TestOption:

    @classmethod
    def setup_class(cls):
        cls.reader = YahooReader("AAPL211217C00085000")

    def test_security_type(self):
        assert self.reader.security_type == "OPTION"
