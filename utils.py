import re

class TickerError(ValueError):
    pass

class DatasetError(KeyError):
    pass

HEADERS = {
        "Connection": "keep-alive",
        "Expires": "-1",
        "Upgrade-Insecure-Requests": "-1",
        "User-Agent": (
            "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        ),
    }

MACROTRENDS_CONVERSION = {
    # Income Statement
    "Revenue": "revenue",
    "Cost Of Goods Sold": "cost of goods sold",
    "Gross Profit": "gross profit",
    "Research And Development Expenses": "r&d expenses",
    "SG&A Expenses": "sg&a expenses",
    "Other Operating Income Or Expenses": "other operating income/expenses",
    "Operating Expenses": "total operating expenses",
    "Operating Income": "operating income",
    "Total Non-Operating Income/Expense": "non-operating income/expenses",
    "Pre-Tax Income": "pretax income",
    "Income Taxes": "income taxes",
    "Income After Taxes": "income after taxes",
    "Other Income": "other income",
    "Income From Continuous Operations": "income from continuous operations",
    "Income From Discontinued Operations": "income from discontinued operations",
    "Net Income": "net income",
    "EBITDA": "ebitda",
    "EBIT": "ebit",
    "Basic Shares Outstanding": "basic shares outstanding",
    "Shares Outstanding": "diluted shares outstanding",
    "Basic EPS": "basic eps",
    "EPS - Earnings Per Share": "diluted eps",

    # Balance Sheet
    "Cash On Hand": "cash and cash equivalents",
    "Receivables": "accounts receivable",
    "Inventory": "inventories",
    "Pre-Paid Expenses": "prepaid expenses",
    "Other Current Assets": "other current assets",
    "Total Current Assets": "total current assets",
    "Property, Plant, And Equipment": "property, plant and equipment",
    "Long-Term Investments": "long-term investments",
    "Goodwill And Intangible Assets": "intangible assets",
    "Other Long-Term Assets": "other non-current assets",
    "Total Long-Term Assets": "total non-current assets",
    "Total Assets": "total assets",
    "Total Current Liabilities": "total current liabilities",
    "Long Term Debt": "non-current debt",
    "Other Non-Current Liabilities": "other non-current liabilities",
    "Total Long Term Liabilities": "total non-current liabilities",
    "Total Liabilities": "total liabilities",
    "Common Stock Net": "common stock and additional paid-in capital",
    "Retained Earnings (Accumulated Deficit)": "retained earnings",
    "Comprehensive Income": "comprehensive income",
    "Other Share Holders Equity": "other shareholders equity",
    "Share Holder Equity": "total shareholders equity",
    "Total Liabilities And Share Holders Equity": "total liabilities and shareholders equity",

    # Cashflow Statement
    "Net Income/Loss": "net income cashflow statement",
    "Total Depreciation And Amortization - Cash Flow": "depreciation and amortization",
    "Other Non-Cash Items": "other non-cash items",
    "Total Non-Cash Items": "total non-cash items",
    "Change In Accounts Receivable": "change in accounts receivable",
    "Change In Inventories": "change in inventories",
    "Change In Accounts Payable": "change in accounts payable",
    "Change In Assets/Liabilities": "change in other assets/liabilities",
    "Total Change In Assets/Liabilities": "total change in assets/liabilities",
    "Cash Flow From Operating Activities": "cashflow from operating activities",
    "Net Change In Property, Plant, And Equipment": "capital expenditures",
    "Net Change In Intangible Assets": "change in intangible assets",
    "Net Acquisitions/Divestitures": "acquisitions/divestitures",
    "Net Change In Short-term Investments": "change in current investments",
    "Net Change In Long-Term Investments": "change in non-current investments",
    "Net Change In Investments - Total": "change in total investments",
    "Investing Activities - Other": "other investing activities",
    "Cash Flow From Investing Activities": "cashflow from investing activities",
    "Net Long-Term Debt": "non-current debt issued/retired",
    "Net Current Debt": "current debt issued/retired",
    "Debt Issuance/Retirement Net - Total": "total debt issued/retired",
    "Net Common Equity Issued/Repurchased": "common stock issued/repurchased",
    "Net Total Equity Issued/Repurchased": "total stock issued/repurchased",
    "Total Common And Preferred Stock Dividends Paid": "total dividends paid",
    "Financial Activities - Other": "other financing activities",
    "Cash Flow From Financial Activities": "cashflow from financing activities",
    "Net Cash Flow": "change in cash and cash equivalents",
    "Stock-Based Compensation": "stock-based compensation",
    "Common Stock Dividends Paid": "dividends paid"
}

CAMEL_TO_SPACE = re.compile(r"(?<!^)(?=[A-Z])")

_YAHOO_CONVERSION = {
    # Income Statement
    "totalRevenue": "revenue",
    "costOfRevenue": "cost of goods sold",
    "grossProfit": "gross profit",
    "researchDevelopment": "r&d expenses",
    "sellingGeneralAdministrative": "sg&a expenses",
    "nonRecurring": "non-recurring expenses",
    "otherOperatingExpenses": "other operating expenses",
    "totalOperatingExpenses": "total operating expenses",
    "operatingIncome": "operating income",
    "totalOtherIncomeExpenseNet": "other income/expenses",
    "ebit": "ebit",
    "interestExpense": "interest expenses",
    "incomeBeforeTax": "income before taxes",
    "incomeTaxExpense": "income taxes",
    "minorityInterest": "minority interest",
    "netIncomeFromContinuingOps": "income from continued operations",
    "discontinuedOperations": "income from discontinued operations",
    "extraordinaryItems": "extraordinary items",
    "effectOfAccountingCharges": "effect of accounting changes",
    "otherItems": "other items",
    "netIncome": "net income",
    "netIncomeApplicableToCommonShares": "net income attributable to common shares",

    # Balance Sheet
    "cash": "cash and cash equivalents",
    "shortTermInvestments": "short-term investments",
    "netReceivables": "acounts receivable",
    "inventory": "inventories",
    "otherCurrentAssets": "other current assets",
    "totalCurrentAssets": "total current assets",
    "longTermInvestments": "non-current investments",
    "propertyPlantEquipment": "property, plant and equipment",
    "goodWill": "goodwill",
    "intangibleAssets": "intagible assets",
    "otherAssets": "other non-current assets",
    "totalAssets": "total assets",
    "accountsPayable": "accounts payable",
    "shortLongTermDebt": "current debt",
    "otherCurrentLiab": "other current liabilities",
    "longTermDebt": "non-current debt",
    "deferredLongTermAssetCharges": "deferred long-term asset charges",
    "deferredLongTermLiab": "deferred long-term liabilities",
    "otherLiab": "other liabilities",
    "totalCurrentLiabilities": "total current liabilities",
    "totalLiab": "total liabities",
    "commonStock": "common stock",
    "retainedEarnings": "retained earnings",
    "treasuryStock": "treasury stock",
    "otherStockholderEquity": "other shareholders equity",
    "totalStockholderEquity": "total shareholders equity",
    "netTangibleAssets": "tangible assets",

    # Cashflow Statement
    "netIncome": "net income",
    "depreciation": "depreciation and amortization",
    "changeToNetincome": "other non-cash items",
    "changeToAccountReceivables": "change in accounts receivable",
    "changeToLiabilities": "change in liabilities",
    "changeToInventory": "change in inventories",
    "changeToOperatingActivities": "other operating activities",
    "effectOfExchangeRate": "gains/losses on currency changes",
    "totalCashFromOperatingActivities": "cashflow from operating activities",
    "capitalExpenditures": "capital expenditures",
    "investments": "change in total investments",
    "otherCashflowsFromInvestingActivities": "other investing activities",
    "totalCashflowsFromInvestingActivities": "cashflow from investing activities",
    "dividendsPaid": "total dividends paid",
    "netBorrowings": "total debt issued/retired",
    "otherCashflowsFromFinancingActivities": "other financing activities",
    "totalCashFromFinancingActivities": "cashflow from financing activities",
    "changeInCash": "change in cash and cash equivalents",
    "repurchaseOfStock": "total stock repurchased",
    "issuanceOfStock": "total stock issued"
}

SERVER_ERROR_MESSAGE = b"<?xml version='1.0' encoding='UTF-8'?><Error><Code>AccessDenied</Code><Message>Access denied.</Message><Details>Anonymous caller does not have storage.objects.get access to the Google Cloud Storage object.</Details></Error>"

PLACEHOLDER_LOGO = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01,\x00\x00\x01,\x08\x03\x00\x00\x00N\xa3~G\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x003PLTE\xbf\xbf\xbf\xdf\xdf\xdf\xd7\xd7\xd7\xef\xef\xef\xf7\xf7\xf7\xc3\xc3\xc3\xe7\xe7\xe7\xc7\xc7\xc7\xcf\xcf\xcf\xfb\xfb\xfb\xf3\xf3\xf3\xcb\xcb\xcb\xe3\xe3\xe3\xd3\xd3\xd3\xeb\xeb\xeb\xdb\xdb\xdb\xff\xff\xff\xe7\x91\xc1\xc3\x00\x00\x00\x11tRNS\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00%\xad\x99b\x00\x00\x07uIDATx\xda\xec\x9c\xdbv\xdb:\x0c\x05u\xb3\xae\x96\xe4\xff\xff\xda\xe3\xb8M\xd2\xb3Z[\x9b\xb2@\x82\xca\xf0)y\xaa:\x02!\x90@\xa6\xb8\xfd^mW$^\xf3rs\xbc\xda\xcb\xfd\x11\x1f?\r\xe5\xa5p\xb0.k\xe3\x14U\xdd?\x1e\xf0\xfeSS\x15nV\xdf:D\xf5\x05\xe8V;B\xe52\xbc\x86\xf2\xfbU\x16\xfe\xd6\xd4\x0e~X\xf9\xc8P/\xc3\xab\x1a\x9d\xe4\xf5\xae\xc8ay\x08\xafLPy\x08\xaf\x8cP\xa5\x0e\xaf\xdcP\xa5\x0b\xaf\xe1\x9a!\xaa4\xe1\xd5\xf8\xff\x02\xbe\x0c\xaf:\x1e\xaa\xb1*r_\xdd5N\xad\xda\xf6\xc5)\xd6\xdc\xda\xef\xbf\xae8\xcd\xb2\xdd\x8e\x8b\xf1\xfe\x9b\xfa\xb5\xbc\xd6u\xfd\x95\x81\xc7\xba\xbe\x96\xb3a(wFGG\xd3\xa0\xea\xab\xb2~\xf1\xd8M]\xceV\xff\xfatx\xfa\x1a\xec2\xd5\xb4\xb6Z\xed3,e\xef\x9f\xd7\xd0\xceV\x01U\xd6\x81EO]N\x8ey\x99\x91\xea\xd6e_u8,\xd5\xc5&\xc4\xdf\xab\xee\x9b\xab\x11\xa9\xf9\xcd\x179\xae\x93\xcd\xf7q\xf7\x0b\\\x8dr\xea|\xc8\x81\xa3\xb9\x1am\xc82\xb0\xa0\x18j\xab\\z\x10)[^\xf7\\*F\xd8\xd8V\x93\xd5\x97\xaf?\xfc\x10k\xc6\xab\xe8\xe6\xadj\xa6\xb2,\x00K\xa3\x02p\xb5,\x00\xe7\x8f2y\xfc\xder\x1fe\xf2\xdaO\x85\xe9\xaa,\x9b\x9eu\x95\xf3-\xc8_Ae~\x87dV\x0bF^\x91Z\x9d\xcd5\xffC~\xcc\x8b\xdc\xbc\xb7\xe3\xa5\x8c\xdc\x10\x1e\xda)\xd7TuM\xd1M\x19s\x0c\xaf.\xd9TFv\xe1\xd5\xa5\x1d`\xc9)\xbc\xba\xf4\xb3>\xce\xc3\xab\xaf\xfd\xa0r\x1e^\xfd\xfd\xb0\xfe\xfb\x0b\xe8h\x1a\xcaex\xf5\x8f{\x8d\x07*G\xd3P\xbf\x8e\x8e\xce\xc2\xeb\xb3\xa7t\xff\xc9\xe3\x1c\xa7\xa7V\xe77\xa0\xa2\xbe\xf9\\N\xc2\xeb\x7f\xdb\xae\xb8\xf9]\xcb\xec\xacD\xf0\x0c+u;\xfd\xaf\xf6\xb7oX\tO\xda\xff\xba\xf8t\x0f\xcb\xb4]\xfc\xbc\xef\xf0\xcf\x8b\xcf\x0c`E\xbf\xf8z:\xdd\x94\x07\xacG\xdf1\x0e\xafWc\x99o\xc1\x1a\xeb\xa5,\xab\xbe\xef\xbf\xff\x1f\xdd\xfd\xb7\xc7`\x8d\xc9H\x90y\xfaz\xddw\xd8\x07k\\\xee\x8c\xb6\x9e\xbc\xaf\xca\xa5\xc9\x89\xd7f\x834\x14\xd6P\x97s\xd0\xe1\xadWGnd^&\xfbQ\x1a\x03\x08\x815^\xab}\xcfy\x99\xcbC\xb7\xe5x\xf0`N\xb7j\x8fW\xc8\xa0\xe677@_\x1e\x19aM;\x1f\xb3!/\x01\x13/\x85\xf4\xe1>\xec\xc1\xda\xe6\xd0\x00\xeb\xdf\x06\x15\xf4\x027a\xd5\x07\xa7\x88\xe9\xd0\x00\xbb\xddS\xe8\xbe\x17\xd9U\xd7\xe0\x07y\t\xcbh\x08\xad[\x8f\x1d\x0c\x18\xdb5(\xc4\xa6*x|q\x0b\xd6`\xd9^\xbf\x1c>H\xd1,\xdb32\x97\x8fj\xe6\x8d\xc0.\x9e\x164\xf6\xa5\xb2\xc5\xe0\xc9\xaf\x91\x99?\xcb\xe4\xe9\xfe[U\x96K\xfd\xfe\xf6/R\xb6\r\xba\xd5\xc9\xdf\xab\xee\x86\xe5\xe4\xd0\x9a\x03\xac\x04\xb7\x93};\xe4\x08+\xd5\xc5d\xd4\xbf\x90{\xe3\xab[\xfcy\'\x99\xf2\xb6\xbb\xf4\xbe\x1d?\xf4\x0e_\xcd\'\\4\xaf\x9bs\xb8h\xe4\x8a\x04\x17\x8d\\\xf0\xe2\xa2\tIV\x9f\xaf\xd2\xe1\x18\x06.\x9a\xc3\xda\x06q\xf3:.\x9a\x93\xa1\xf2\x10^\xb8hN\x8b*]x\xe1\xa2\xd1\xeb*\\4\xf2y\x19\x17\x8d\x9c\xaap\xd1\xc8\xfb\x0f\x17\x8d<Ha\x9c{q\xd1H\xd7\x03\xb8h\xb4\x87\xc5E#\x06\x14.\x1a\xb9\xed\x8e\x8bF\xfbn\xe3\xa2\x91+\x1c\\41I\xd9\xf2\xc2E\x13\x9cSq\xd1\x04\xbf^\\4\xbe\x0f\xf9\xb8h\xf4L\x15\xe7\x92\r\x17\xcd\x0f\xda\x8e\xb8h\x02\xee#q\xd1\xa8\xa8p\xd1\xf8G\x95]x\xe1\xa2\xd9,\x11p\xd1\xe8\xa8p\xd1\x04\xa0\xc2E\xa3\x15\x9e\xb8hdT\xb8h\xe4\x1a\x1d\x17\xcd\xbe\x12\x01\x17\xcdv\xaa\xca\x04\xd6\r\x17\x8d\x9fv\xf1\xf3\xbe\x03.\x1a\xf96\x01\x17\x8d\xda\x884r\xd1\xc4\xfe:\xe6\xe9\xa29\'\xaf\xc3]4\x0ex\xe5\xe1\xa2\xf1\x93\xbf\x9c\xbbh\xdc}\x1f\xbd\xbah\xfc\x06\x987\x17\x8d\xf7\x02\xdf\x8d\x8b&\x97\x08K\xef\xa2\xc9-\x89%t\xd1d\xbb-\xa3\xbbh\xe4\xf8\x8fk\x93L\xbe2\xb3I\xe6\x05+\xbdM2\x13Xnl\x92\xdeay\xb3I\xba\x85\xe5\xd5&\xe9\x0f\x96s\x9b\xa4\x1fX\x99\xd8$\x1d\xc0\xca\xcc&\x99\x12V\xae6\xc9\xf8\xb0\xb0I\xaa\xb0\xb0I\xca\xb0\xb0I\xaa\xb0\xb0I\xbe.\xcc\xb1I\xca\xa7bl\x92\xf2\xc2&\xa9\xdf)b\x93\x94\xaf\xac\xb1I\x86$\xab\xcfW\xe9p\x90\x1a\x9b\xe4a\x83?q\xf3:6\xc9\x93\xa1\xf2\x10^\xd8$O\x8b*]xa\x93\xd4\xeb*l\x92\xf2y\x19\x9b\xa4\x9c\xaa\xb0I\xca\xfb\x0f\x9b\xa4\xb8\xb0I\xba\x08*l\x92\xe2\xc3b\x93T\xc7;\xb0I\xaamwl\x92\xdaw\x1b\x9b\xa4\\\xe1`\x93\x8cI\xca\x96\x176\xc9\xe0\x9c\x8aM2\xf8\xf5b\x93\xf4}\xc8\xc7&\xa9g\xaa8\x97l\xd8$\x7f\xd0v\xc4&\x19p\x1f\x89MRE\x85M\xd2?\xaa\xec\xc2\x0b\x9b\xe4f\x89\x80MRG\x85M2\x00\x156I\xad\xf0\xc4&)\xa3\xc2&)\xd7\xe8\xd8$\xf7\x95\x08\xd8$\xb7SU&\xb0n\xd8$\xfd\xb4\x8b\x9f\xf7\x1d\xb0I\xca\xb7\t\xd8$\xd5F$6\xc9C\xfa\x0e\xd8$\x03\x1a\xa4\xd8$\x03\xc6\x00\xb0I\x16\xd8$\xf5\x90\xc2&)\x83\xc2&)m=l\x92\xd2\xc2&\x89Mr\xc7\xb6\xc4&\xe9da\x934\x84\x85MR\x8d\'l\x92*(l\x92\xd8$\x0f\x85\x85MR\x84\x85MR\x85\x85MR\x86\x85MR\x85\x85MR\x85\x85MR\x86\x85MR\x85\x85M\xf2ua\x8eMR>\x15c\x93\x94\x176I\xfdN\x11\x9b\xa4|e\x8dM2$Y}\xbeJ\x87\x83\xd4\xd8$\x0f\x1b\xfc\x89\x9b\xd7\xb1I\x9e\x0c\x95\x87\xf0\xc2&yZT\xe9\xc2\x0b\x9b\xa4^Wa\x93\x94\xcf\xcb\xd8$\xe5T\x85MR\xde\x7f\xd8$\xc5\x85M\xd2EPa\x93\x14\x1f\x16\x9b\xa4:\xde\x81MRm\xbbc\x93\xd4\xbe\xdb\xd8$\xe5\n\x07\x9bdLR\xb6\xbc\xb0I\x06\xe7Tl\x92\xc1\xaf\x17\x9b\xa4\xefC>6I=S\xc5\xb9d\xc3&\xf9\x83\xb6#6\xc9\x80\xfbHl\x92**l\x92\xfeQe\x17^\xd8$7K\x04l\x92:*l\x92\x01\xa8\xb0Ij\x85\'6I\x19\x156I\xb9F\xc7&\xb9\xafD\xc0&\xb9\x9d\xaa2\x81u\xc3&\xe9\xa7]\xfc\xbc\xef\x80MR\xbeM\xc0&\xa96"\x8dl\x92O]4\xa5\x89\x8b&S\x9bd2\x17M^6\xc9\xf4.\x9aLl\x92n\\4\xdem\x92\xde\\4nm\x92^]4\xfel\x92\xce]4~l\x92\x99\xb8h\x1c\xd8$3s\xd1\xa4\xb4I\xe6\xea\xa2\x89o\x93\xc4E\xa3\xc2\xc2E#\xc3\xc2E\xa3\xc2\xc2E\xf3\xfa\xab\x8b\x8bF>\x15\xe3\xa2\xd1\x9bs\xb8h\xe4\x8a\x04\x17\x8d\\\xf0\xe2\xa2\tIV\x9f\xaf\xd2\xe1\x18\x06.\x9a\xc3\xda\x06q\xf3:.\x9a\x93\xa1\xf2\x10^\xb8hN\x8b*]x\xe1\xa2\xd1\xeb*\\4\xf2y\x19\x17\x8d\x9c\xaap\xd1\xc8\xfb\x0f\x17\x8d<Ha\x9c{q\xd1H\xd7\x03\xb8h\xb4\x87\xc5E#\x06\x14.\x1a\xb9\xed\x8e\x8bF\xfbn\xe3\xa2\x91+\x1c\\41I\xd9\xf2\xc2E\x13\x9cSq\xd1\x04\xbf^\\4\xbe\x0f\xf9\xb8h\xf4L\x15\xe7\x92\r\x17\xcd\x0f\xda\x8e\xb8h\x02\xee#q\xd1\xa8\xa8p\xd1\xf8G\x95]x\xe1\xa2\xd9,\x11p\xd1\xe8\xa8p\xd1\x04\xa0\xc2E\xa3\x15\x9e\xb8hdT\xb8h\xe4\x1a\x1d\x17\xcd\xbe\x12\xe1?\x01\x06\x00\xe2\xea\x01"Ko\x03m\x00\x00\x00\x00IEND\xaeB`\x82'