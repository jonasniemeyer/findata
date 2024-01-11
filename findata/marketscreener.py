from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from . import utils


class MarketscreenerReader:
    _base_url = "https://www.marketscreener.com"
    
    def __init__(self, identifier) -> None:
        params = {"q": identifier}
        html = requests.get(url=f"{self._base_url}/search/", params=params, headers=utils.HEADERS).text
        soup = BeautifulSoup(html, "lxml")
        
        try:
            company_tag = soup.find("table", {"class": "table table--small table--hover table--bordered table--fixed"}).find("tbody").find("tr").find_all("td")[1].find("span").find("a")
        except AttributeError:
            raise utils.DatasetError(f"no stock found for identifier '{identifier}'")
        
        self._company_url = f"{self._base_url}{company_tag.get('href')}"
        self._header_parsed = False

    def _get_company_information(self) -> None:
        url = f"{self._company_url}company/"
        html = requests.get(url=url, headers=utils.HEADERS).text
        self._company_soup = BeautifulSoup(html, "lxml")

    def _get_financial_information(self) -> None:
        url = f"{self._company_url}finances/"
        html = requests.get(url=url, headers=utils.HEADERS).text
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
        ticker, isin = header.find("div", {"class": "mt-10 py-5 py-m-0 mt-m-5 c-flex align-center badge-container"}).find_all("h2", recursive=False)
        self._ticker = ticker.text.strip()
        self._isin = isin.text.strip()

        self._name = header.find("h1").text.replace("Financials", "").replace("Company", "").strip()

        price_tag = header.find("span", {"class": "last txt-bold js-last"})
        self._price = float(price_tag.text)
        self._currency = price_tag.find_next("sup").text.strip()

        self._header_parsed = True

    def board_members(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        board_members = []
        
        rows = self._company_soup.find("h3", string=re.compile(r"\s*Members of the board\s*")).find_next("tbody").find_all("tr")
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
                joined = pd.to_datetime(joined).date().isoformat()
            
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
            raise utils.DatasetError(f"no country data found for stock '{self.name}'")
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
            header = self._financial_soup.find("h3", string="Income Statement Evolution (Quarterly data)")
        else:
            header = self._financial_soup.find("h3", string="Income Statement Evolution (Annual data)")

        rows = header.find_next("tbody").find_all("tr")
        years = header.find_next("thead").find("tr").find_all("th")[1:]
        years = {
            index: tag.find("span").text.strip()
            for index, tag in enumerate(years)
        }

        if not quarterly:
            years = {
                index: int(year)
                for index, year in years.items()
            }

        data = {}
        for year in sorted(years.values(), reverse=True):
            data[year] = {}
        for row in rows[:-1]:
            cells = row.find_all("td")
            name = cells[0].find(string=True).strip()
            if name == "FCF margin":
                name = "FCF Margin"
            elif name not in ("EBITDA", "EBIT", "EPS", "FCF Conversion (EBITDA)", "FCF Conversion (Net income)"):
                name = name.title()

            if "(" in name:
                name = name[:name.index(" (")]

            for index, cell in enumerate(cells[1:]):
                year = years[index]

                if cell.text.strip() == "-":
                    value = None
                else:
                    value = cell.text.replace(" ", "").replace(",", ".").strip()
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
            header = self._financial_soup.find("h3", string="Balance Sheet Analysis")
            rows = header.find_next("tbody").find_all("tr")
            years = header.find_next("thead").find("tr").find_all("th")[1:]
            years = {
                index: int(tag.find("span").text.strip())
                for index, tag in enumerate(years)
            }

            for year in sorted(years.values(), reverse=True):
                if year not in data:
                    data[year] = {}
            
            for row in rows[:-1]:
                cells = row.find_all("td")
                name = cells[0].find(string=True).strip().title()
                if name not in (
                    "Net Cash Position"
                    "Free Cash Flow",
                    "Shareholders' Equity",
                    "Assets",
                    "Book Value Per Share",
                    "Cash Flow Per Share",
                    "Capex"
                ):
                    continue
                for index, cell in enumerate(cells[1:]):
                    year = years[index]
                    if cell.text.strip() == "-":
                        value = None
                    else:
                        value = cell.text.replace(" ", "").replace(",", ".").strip()
                        if name in ("Book Value Per Share", "Cash Flow Per Share"):
                            value = float(value)
                        else:
                            value = int(float(value) * 1e6)
                    data[year][name] = value

                    analysts = cell.get("title")
                    if analysts is not None:
                        analysts = int(re.findall("Number of financial analysts who provided an estimate : ([0-9]+)", analysts)[0])
                    data[year][f"{name} Analysts"] = analysts

            header = self._financial_soup.find("h3", string="Valuation")
            if header is None:
                for year in data:
                    data[year]["Shares Outstanding"] = None
            else:
                rows = header.find_next("tbody").find_all("tr")
                years = header.find_next("thead").find("tr").find_all("th")[1:]
                years = {
                    index: int(tag.find("span").text)
                    for index, tag in enumerate(years)
                }

                for year in sorted(years.values(), reverse=True):
                    if year not in data:
                        data[year] = {}

                for row in rows[:-1]:
                    cells = row.find_all("td")
                    name = cells[0].find(string=True).strip()
                    if name != "Nbr of stocks (in thousands)":
                        continue
                    for index, cell in enumerate(cells[1:]):
                        year = years[index]
                        if cell.text.strip() == "-":
                            value = None
                        else:
                            value = int(float(cell.text.strip().replace(" ", "").replace(",", "")) * 1e3)
                        data[year]["Shares Outstanding"] = value
        
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
        rows = self._company_soup.find("h3", string=re.compile(r"\s*Managers\s*")).find_next("tbody").find_all("tr")
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
                joined = pd.to_datetime(joined).date().isoformat()
            
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
            "all": ("news-history", "All News"),
            "analysts": ("news-broker-research", "Analyst Reco."),
            "highlights": ("news-key-events", "Highlights"),
            "insiders": ("news-insiders", "Insiders"),
            "transcripts": ("news-call-transcripts", "Transcripts"),
            "press_releases": ("news-press-releases", "Press Releases"),
            "official_publications": ("news-publications", "Official Publications"),
            "other_languages": ("news-other-languages", "Other languages")
        }

        if news_type not in news_types:
            raise ValueError(f"news_type has be one of the following: {tuple(news_types.keys())}")
        
        if isinstance(start, str):
            start = pd.to_datetime(start).timestamp()
        elif not isinstance(start, (int, float)):
            raise ValueError("start parameter has to be of type str, float or int")        
        
        source, header = news_types[news_type]
        articles = []
        url = f"{self._company_url}{source}/"
        html = requests.get(url=url, headers=utils.HEADERS).text
        soup = BeautifulSoup(html, "lxml")

        rows = soup.find("h3", string=header).find_next("table").find_all("tr")
        for row in rows:
            cells = row.find_all("td")

            title = cells[0].find("a").text.strip()
            url = cells[0].find("a").get("href")
            url = f"{self._base_url}{url}"

            date = cells[1].find("time").get("datetime")
            date = pd.to_datetime(pd.to_datetime(date))
            if timestamps:
                date = int(date.timestamp())
            else:
                date = date.isoformat()

            source_tag = cells[2].find("span")
            news_source = source_tag.get("title").replace("@", "")
            news_source_abbr = source_tag.find("span").text.strip()
            if news_source_abbr == "":
                news_source_abbr = None
            
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
            
        return articles

    def segment_information(self) -> dict:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        header = self._company_soup.find("h3", string="Sales per Business")
        if header is None:
            raise utils.DatasetError(f"no segment data found for stock '{self.name}'")
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
                data[years[index]][name] = float(cell.text.strip().replace(",", ".")) * 1e7 if cell.text != "-" else None
        
        return data

    def shareholders(self) -> list:
        if not hasattr(self, "_company_soup"):
            self._get_company_information()
        
        shareholders = []
        rows = self._company_soup.find("h3", string="Shareholders").find_next("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            company = cells[0].find("div").find("span").text.strip()
            shares = int(cells[1].text.replace(",", ""))
            percentage = round(float(cells[2].text.replace("%", ""))/100, 4)
            value = cells[3].text
            if "B" in value:
                value = value.replace("B", "")
                multiplier = 1e9
            elif "M" in value:
                value = value.replace("M", "")
                multiplier = 1e6
            value = int(value.replace("$", "").replace(" ", "").strip()) * multiplier
            
            shareholders.append(
                {
                    "company": company,
                    "shares": shares,
                    "percentage": percentage,
                    "value": value
                }
            )
        
        return shareholders

    def ticker(self) -> str:
        self._parse_header()
        return self._ticker