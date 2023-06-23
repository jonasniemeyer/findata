import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from findata.utils import HEADERS, DatasetError

class MarketscreenerReader:
    _base_url = "https://www.marketscreener.com"
    
    def __init__(self, identifier) -> None:
        params = {"q": identifier}
        html = requests.get(url=f"{self._base_url}/search/", params=params, headers=HEADERS).text
        soup = BeautifulSoup(html, "lxml")
        
        try:
            company_tag = soup.find("table", {"class": "table table--small table--hover table--centered table--bordered"}).find("tbody").find_all("tr")[0].find("td").find("a")
        except AttributeError:
            raise DatasetError(f"no stock found for identifier '{identifier}'")
        
        self._company_url = f"{self._base_url}{company_tag.get('href')}"
        self._header_parsed = False

    def _get_company_information(self) -> None:
        url = f"{self._company_url}company/"
        html = requests.get(url=url, headers=HEADERS).text
        self._company_soup = BeautifulSoup(html, "lxml")

    def _get_financial_information(self) -> None:
        url = f"{self._company_url}financials/"
        html = requests.get(url=url, headers=HEADERS).text
        self._financial_soup = BeautifulSoup(html, "lxml")

    def _parse_header(self) -> None:
        if self._header_parsed:
            return

        if hasattr(self, "_financial_soup"):
            soup = self._financial_soup
        elif hasattr(self, "_company_soup"):
            soup = self._company_soup
        else:
            self._get_financial_information()
            soup = self._financial_soup

        header = soup.find("div", {"class": "card-content p-10"})
        ticker, isin = header.find("div", {"class": "c-12 cm-auto grid align-center"}).find_all("span")[:2]
        self._ticker = ticker.text.strip()
        self._isin = isin.text.strip()

        self._name = header.find("h1").text.strip()

        price_tag = header.find("span", {"class": "last no-animation txt-bold js-last"})
        self._price = float(price_tag.text)
        self._currency = price_tag.find_next("sup").text.strip()

        self._header_parsed = True

    def board_members(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        board_members = []
        
        rows = self._company_soup.find("h3", string=re.compile("\s*Members of the board\s*")).find_next("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            name = cells[0].find("div").find("a").text.strip()
            title = cells[1].text.strip()
            age = cells[2].text
            if age == "-":
                age = None
            else:
                age = int(age)
            joined = cells[3].text
            if joined == "-":
                joined = None
            else:
                joined = int(joined)
            
            board_members.append(
                {
                    "name": name,
                    "title": title,
                    "age": age,
                    "joined": joined
                }
            )
        
        return board_members

    def country_information(self) -> dict:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()

        header = self._company_soup.find("h3", string="Sales per region")
        if header is None:
            raise DatasetError(f"no country data found for stock '{self.name}'")
        else:
            headers = header.find_next("thead").find("tr").find_all("th")
            rows = header.find_next("tbody").find_all("tr")

        years = {
            index: int(tag.text)
            for index, tag in enumerate(headers[1:-1:2])
        }
        data = {}
        for year in sorted(years.values(), reverse=True):
            data[year] = {}

        for row in rows:
            cells = row.find_all("td")
            name = cells[0].find("div").find("span").text.strip()
            for index, cell in enumerate(cells[1:-1:2]):
                data[years[index]][name] = float(cell.text.strip().replace(",", ".")) * 1e6 if cell.text != "-" else None
        
        return data

    def currency(self) -> str:
        self._parse_header()
        return self._currency

    def financial_statement(self, quarterly=False) -> list:
        if not hasattr(self, "_financial_soup"):
            self._get_financial_information()
        
        if quarterly:
            rows = self._financial_soup.find("b", string="Income Statement Evolution (Quarterly data)").find_next("tr").find("td", recursive=False).find("table").find_all("tr")
            years = {
                index+1: tag.find("b").text
                for index, tag in enumerate(rows[0].find_all("td")[1:])
            }
        else:
            rows = self._financial_soup.find("b", string="Income Statement Evolution (Annual data)").find_next("tr").find("td", recursive=False).find("table").find_all("tr")
            years = {
                index+1: int(tag.find("b").text)
                for index, tag in enumerate(rows[0].find_all("td")[1:])
            }
        data = {}
        for year in sorted(years.values(), reverse=True):
            data[year] = {}

        for row in rows[1:-3]:
            cells = row.find_all("td")
            name = cells[0].find(text=True)
            if name == "FCF margin":
                name = "FCF Margin"
            elif name not in ("EBITDA", "EPS", "FCF Conversion"):
                name = name.title()

            if "(" in name:
                name = name[:name.index(" (")]

            for index, cell in enumerate(cells[1:]):
                year = years[index+1]

                if cell.text == "-":
                    value = None
                else:
                    value = cell.text.replace(" ", "").replace(",", ".")
                    if name in ("Operating Margin", "Net Margin", "FCF Margin", "FCF Conversion"):
                        value = float(value.replace("%", ""))  / 100
                    elif name in ("EPS", "Dividend Per Share"):
                        value = float(value)
                    else:
                        value = int(float(value) * 1e6)
                data[year][name] = value

                analysts = cell.get("title")
                if analysts is not None:
                    analysts = int(re.findall("Number of financial analysts who provided an estimate : ([0-9]+)", analysts)[0])
                data[year][f"{name} Analysts"] = analysts
        
        # if annual data is parsed, parse also Balance Sheet and Cashflow Items
        if not quarterly:
            rows = self._financial_soup.find("b", string="Balance Sheet Analysis").find_next("tr").find("td", recursive=False).find("table").find_all("tr")
            years = {
                index+1: int(tag.find("b").text)
                for index, tag in enumerate(rows[0].find_all("td")[1:])
            }
            for year in sorted(years.values(), reverse=True):
                if year not in data:
                    data[year] = {}
            
            for row in rows[1:-3]:
                cells = row.find_all("td")
                name = cells[0].find(text=True).title()
                if name not in (
                    "Free Cash Flow",
                    "Shareholders' Equity",
                    "Assets",
                    "Book Value Per Share",
                    "Cash Flow Per Share",
                    "Capex"
                ):
                    continue
                for index, cell in enumerate(cells[1:]):
                    year = years[index+1]
                    if cell.text == "-":
                        value = None
                    else:
                        value = cell.text.replace(" ", "").replace(",", ".")
                        if name in ("Book Value Per Share", "Cash Flow Per Share"):
                            value = float(value)
                        else:
                            value = int(float(value) * 1e6)
                    data[year][name] = value

                    analysts = cell.get("title")
                    if analysts is not None:
                        analysts = int(re.findall("Number of financial analysts who provided an estimate : ([0-9]+)", analysts)[0])
                    data[year][f"{name} Analysts"] = analysts
            
            header = self._financial_soup.find("b", string="Valuation")
            if header is None:
                for year in data:
                    data[year]["Shares Outstanding"] = None
            else:
                rows = header.find_next("tr").find("td", recursive=False).find("table").find_all("tr")
                years = {
                    index+1: int(tag.find("b").text)
                    for index, tag in enumerate(rows[0].find_all("td")[1:])
                }
                for year in sorted(years.values(), reverse=True):
                    if year not in data:
                        data[year] = {}

                for row in rows[1:-3]:
                    cells = row.find_all("td")
                    name = cells[0].find(text=True)
                    if name != "Nbr of stocks (in thousands)":
                        continue
                    name = "Shares Outstanding"
                    for index, cell in enumerate(cells[1:]):
                        year = years[index+1]
                        if cell.text == "-":
                            value = None
                        else:
                            value = int(float(cell.text.replace(" ", "").replace(",", ".")) * 1e3)
                        data[year][name] = value
        
        return data

    def industry_information(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()

        industries = []
        rows = self._company_soup.find("h3", string="Sector").find_next("div").find("table").find_all("tr")
        for row in rows:
            industry = row.find_all("td")[-1].find("a").text.strip()
            industries.append(industry)
        
        self._industry = industries[-1]
        
        return industries

    def isin(self) -> str:
        self._parse_header()
        return self._isin

    def latest_price(self) -> float:
        self._parse_header()
        return self._price

    def managers(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        managers = []
        rows = self._company_soup.find("h3", string=re.compile("\s*Managers\s*")).find_next("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            name = cells[0].find("div").find("a").text.strip()
            title = cells[1].text.strip()
            age = cells[2].text.strip()
            if age == "-":
                age = None
            else:
                age = int(age)
            joined = cells[3].text.strip()
            if joined == "-":
                joined = None
            else:
                joined = int(joined)
            
            managers.append(
                {
                    "name": name,
                    "title": title,
                    "age": age,
                    "joined": joined
                }
            )
        
        return managers

    def name(self) -> str:
        self._parse_header()
        return self._name

    def news(
        self,
        news_type="all",
        start=pd.to_datetime("today").date().isoformat(),
        timestamps=False
    ) -> list:
        news_types = {
            "most_relevant": ("news-quality", "Most relevant news about"),
            "all": ("news-history", "All news about"),
            "analysts": ("news-broker-research", "Analyst Recommendations on"),
            "other_languages": ("news-other-languages", "News in other languages on"),
            "press_releases": ("news-communiques", "Communiqués de presse de la société"),
            "official_publications": ("news-publications", "Official Publications"),
            "sector": ("news-sector", "Sector news")
        }
        if news_type not in news_types:
            raise ValueError(f"news_type has be one of the following: {tuple(news_types.keys())}")
        
        if isinstance(start, str):
            start = pd.to_datetime(start).timestamp()
        elif not isinstance(start, (int, float)):
            raise ValueError("start parameter has to be of type str, float or int")        
        
        source = news_types[news_type][0]
        if news_type == "sector":
            if not hasattr(self, "_industry"):
                self.industry_information()
            header = f"{news_types[news_type][1]} {self._industry}"
        elif news_type == "official_publications":
            header = news_types[news_type][1]
        else:
            header = f"{news_types[news_type][1]} {self.name()}"
        
        articles = []
        start_reached = False
        page_counter = 0
        
        while start_reached is False:
            page_counter+=1
            url = f"{self._company_url}{source}/fpage={page_counter}"
            html = requests.get(url=url, headers=HEADERS).text
            soup = BeautifulSoup(html, "lxml")
            
            rows = soup.find("b", string=header).find_next("tr").find("td", recursive=False).find("table").find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                date = cells[0].text
                if ":" in date:
                    date =  pd.to_datetime("today")
                elif "/" in date:
                    current_year = pd.to_datetime("today").year
                    date =  pd.to_datetime(f"{date}/{current_year}")
                else:
                    date = pd.to_datetime(f"{date}-01-01")

                if date.timestamp() < start:
                    start_reached = True
                    break
                
                if timestamps:
                    date = int(date.timestamp())
                else:
                    date = date.date().isoformat()
                
                url = cells[1].find("a").get("href")
                url = f"{self._base_url}{url}"
                title = cells[1].find("a").text
                if cells[1].find("a").find("b") is not None:
                    title = title.replace(" :", ":")
                news_source = cells[2].find("div")
                if news_source is None:
                    news_source = None
                    news_source_abbr = None
                else:
                    news_source_abbr = news_source.text
                    news_source = news_source.get("title").replace("©", "")
                
                articles.append(
                    {
                        "title": title,
                        "date": date,
                        "source": {
                            "name": news_source,
                            "abbreviation": news_source_abbr
                        },
                        "url": url
                    }
                )
            
            
            pages_nav = soup.find("span", {"class": "nPageTable"})
            if (pages_nav is None) or (pages_nav.find("a", {"class": "nPageEndTab"}) is None):
                start_reached = True
            
        return articles

    def segment_information(self) -> dict:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        header = self._company_soup.find("h3", string="Sales per Business")
        if header is None:
            raise DatasetError(f"no segment data found for stock '{self.name}'")
        else:
            headers = header.find_next("thead").find("tr").find_all("th")
            rows = header.find_next("tbody").find_all("tr")

        years = {
            index: int(tag.text)
            for index, tag in enumerate(headers[1:-1:2])
        }
        data = {}
        for year in sorted(years.values(), reverse=True):
            data[year] = {}

        for row in rows:
            cells = row.find_all("td")
            name = cells[0].find("div").find("span").text.strip()
            for index, cell in enumerate(cells[1:-1:2]):
                data[years[index]][name] = float(cell.text.strip().replace(",", ".")) * 1e6 if cell.text != "-" else None
        
        return data

    def shareholders(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        shareholders = []
        rows = self._company_soup.find("b", string="Shareholders").find_next("tr").find("td", recursive=False).find("table").find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            company = cells[0].text.strip()
            shares = int(cells[1].text.replace(",", ""))
            percentage = round(float(cells[2].text.replace("%", ""))/100, 4)
            
            shareholders.append(
                {
                    "company": company,
                    "shares": shares,
                    "percentage": percentage
                }
            )
        
        return shareholders

    def ticker(self) -> str:
        self._parse_header()
        return self._ticker

if __name__ == "__main__":
    print(MarketscreenerReader("AAPL").segment_information())