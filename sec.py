import requests
import re
import datetime as dt
import pandas as pd
from finance_data.utils import HEADERS, DatasetError
from typing import Union
from bs4 import BeautifulSoup

def sec_companies() -> list:
    items = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS).json()
    items = [
        {
            "cik": item["cik_str"],
            "ticker": item["ticker"],
            "name": item["title"],
        }
        for _, item in items.items()
    ]
    return items

def sec_mutualfunds() -> list:
    items = requests.get("https://www.sec.gov/files/company_tickers_mf.json", headers=HEADERS).json()["data"]
    items = [
        {
            "ticker": item[3].replace("(", "").replace(")", ""),
            "class_cik": item[2],
            "series_cik": item[1],
            "entity_cik": item[0]
        }
        for item in items
    ]
    return items

def latest_sec_filings(start=pd.to_datetime("today").isoformat(), timestamps=False) -> list:
    filings = []
    start_reached = False
    page_counter = 0

    while not start_reached:
        params = {
            "action": "getcurrent",
            "start": page_counter,
            "count": 100
        }
        html = requests.get(url="https://www.sec.gov/cgi-bin/browse-edgar", params=params, headers=HEADERS).text
        soup = BeautifulSoup(html, "lxml")
        tables = soup.find_all("table")
        if len(tables) != 8:
            break

        entries = tables[-2].find_all("tr")[1:]
        for index in range(0, len(entries), 2):
            name = entries[index].find_all("td")[-1].text.strip()
            name, cik = re.findall("(.+) \(([0-9]{,10})\) \([A-Za-z ]+\)", name)[0]
            cik = int(cik)

            cells = entries[index+1].find_all("td")
            form_type = cells[0].text
            url = cells[1].find_all("a")[-1].get("href")
            url = f"https://www.sec.gov{url}"
            accession_number = cells[2].text
            accession_number = re.findall("Accession Number: ([0-9-]+)", accession_number)[0]
            accepted = cells[3].text
            accepted = re.sub("([0-9]{4}-[0-9]{2}-[0-9]{2})([0-9]{2}:[0-9]{2}:[0-9]{2})", r"\1T\2", accepted)

            if pd.to_datetime(accepted) < pd.to_datetime(start):
                start_reached = True
                break

            date_filed = cells[4].text

            if timestamps:
                accepted = int(pd.to_datetime(accepted).timestamp())
                date_filed = int(pd.to_datetime(date_filed).timestamp())

            if len(cells) == 6:
                file_number, film_number = cells[5].text.split("\n")
                film_number = None if film_number == "" else int(film_number)
            else:
                file_number = None
                film_number = None

            filings.append(
                {
                    "name": name,
                    "cik": cik,
                    "form_type": form_type,
                    "url": url,
                    "accession_number": accession_number,
                    "accepted": accepted,
                    "date_filed": date_filed,
                    "file_number": file_number,
                    "film_number": film_number
                }
            )
        page_counter += 100

    return filings


class _SECFiling:
    """
    _SECFiling is the parent class for all SEC filing classes and should never be called.
    It splits the file into the header and document section and extracts information in the header section.
    
    The header section contains file-related information such as the date and to what entities the file relates to.
    Assertion that the entity exists (e.g. issuer in Form 4 Filings) is done by the respective subclass.
    The header also holds entity-specific information (e.g. the name and the CIK) whose parsing is also done in the _SECFiling parent class.
    
    The document section holds the file-specific data (e.g. fund holdings in Form 13F filings) and parsing is solely governed by the respective subclass.
    
    Each SEC filing, irrespective of the type, has the following attributes:
        accession_number: str        
        date_filed: str
        date_of_period: str
        date_of_change: str
        document: str
        document_count: int
        effectiveness_date: str
        file: str
        file_number: str
        film_number: int
        header: str
        is_amendment: bool
        is_html: bool
        is_xml: bool
        submission_type: str
    
    If only the url is available and not the file string, the classmethod from_url can be called to pull the data from the web first.
    """
    
    def __init__(self, file: str) -> None:
        self._file = file.replace("&nbsp;", " ")
        if "<SEC-HEADER>" in self.file:
            header_open, header_close = "<SEC-HEADER>", "</SEC-HEADER>"
        elif "<IMS-HEADER>" in self.file:
            header_open, header_close = "<IMS-HEADER>", "</IMS-HEADER>"
        else:
            raise DatasetError(f"Could not find a header section")
        self._header = self._file[self.file.find(header_open):self.file.find(header_close)] + header_close
        self._document = self.file[self.file.find("<DOCUMENT>"):self.file.find("</SEC-DOCUMENT>")]
        
        self._is_html = True if ("<html>" in self.file or "<HTML>" in self.file) else False
        self._is_xml = True if ("<xml>" in self.file or "<XML>" in self.file) else False
        
        file_number = re.findall("SEC FILE NUMBER:\t([0-9\-]+)", self.header)
        if len(file_number) == 0:
            file_number = None
        else:
            self._file_number = file_number[0]
        
        film_number = re.findall("FILM NUMBER:\t{2}([0-9\-]+)", self.header)
        if len(film_number) == 0:
            film_number = None
        else:
            self._film_number = int(film_number[0])
        
        self._parse_header_entities()
        
    def _parse_header_entities(self) -> None:
        """
        There are 4 different possible header entities: Filer, Subject Company, Reporting Owner, Issuer
        Some documents only have a filer entity (e.g. Form 10-K), some documents have filer and subject entities (e.g. Form 13D) and some have
        reporting owner and issuer entities (e.g. Form 4).
        
        This method splits the header section into subsections of each entity and parses the respective section if it exists.
        """
        
        self._document_count = int(re.findall("PUBLIC DOCUMENT COUNT:\t{2}([0-9]+)", self.header)[0])
        self._accession_number = re.findall("ACCESSION NUMBER:\t{2}([0-9\-]+)", self.header)[0]
        self._submission_type = re.findall("CONFORMED SUBMISSION TYPE:\t(.+)", self.header)[0]
        self._is_amendment = True if self.submission_type.endswith("/A") else False
        
        date_filed = re.findall("FILED AS OF DATE:\t{2}([0-9]{8})", self.header)[0]
        date_filed = dt.date(
            year=int(date_filed[:4]),
            month=int(date_filed[4:6]),
            day=int(date_filed[6:8])
        ).isoformat()
        self._date_filed = date_filed
        
        date_of_period = re.findall("CONFORMED PERIOD OF REPORT:\t([0-9]{8})", self.header)
        if len(date_of_period) == 0:
            date_of_period = None
        else:
            date_of_period = date_of_period[0]
            date_of_period = dt.date(
                year=int(date_of_period[:4]),
                month=int(date_of_period[4:6]),
                day=int(date_of_period[6:8])
            ).isoformat()
        self._date_of_period = date_of_period

        date_of_change = re.findall("DATE AS OF CHANGE:\t{2}([0-9]{8})", self.header)
        if len(date_of_change) == 0:
            date_of_change = None
        else:
            date_of_change = date_of_change[0]
            date_of_change = dt.date(
                year=int(date_of_change[:4]),
                month=int(date_of_change[4:6]),
                day=int(date_of_change[6:8])
            ).isoformat()
            self._date_of_change = date_of_change

        effectiveness_date = re.findall("EFFECTIVENESS DATE:\t{2}([0-9]{8})", self.header)
        if len(effectiveness_date) == 0:
            effectiveness_date = None
        else:
            effectiveness_date = effectiveness_date[0]
            effectiveness_date = dt.date(
                year=int(effectiveness_date[:4]),
                month=int(effectiveness_date[4:6]),
                day=int(effectiveness_date[6:8])
            ).isoformat()
        self._effectiveness_date = effectiveness_date
        
        indices = []
        
        filer_indices = [item.start() for item in re.finditer("FILER:", self.header)]
        if len(filer_indices) == 0:
            filer_indices = [item.start() for item in re.finditer("FILED BY:", self.header)]
        
        for index in filer_indices:
            indices.append(index)
        
        subject_index = self.header.find("SUBJECT COMPANY:") 
        if subject_index != -1:
            indices.append(subject_index)
        
        reporting_owner_indices = [item.start() for item in re.finditer("REPORTING-OWNER:", self.header)]
        for index in reporting_owner_indices:
            indices.append(index)
        
        issuer_index = self.header.find("ISSUER:")
        if issuer_index != -1:
            indices.append(issuer_index)
        
        indices = sorted(indices)
        
        self._filer = self._parse_header_subsection(filer_indices, indices)
        self._subject_company = self._parse_header_subsection(subject_index, indices)
        self._reporting_owner = self._parse_header_subsection(reporting_owner_indices, indices)
        self._issuer = self._parse_header_subsection(issuer_index, indices)
    
    def _parse_header_subsection(self, index: Union[int, list], indices: list) -> Union[list, dict, None]:
        if isinstance(index, list):
            data = []
            if len(index) != 0:
                for item in index:
                    if indices.index(item)+1 == len(indices):
                        subsection = self.header[item:]
                    else:
                        subsection = self.header[item:indices[indices.index(item)+1]]
                    data.append(self._parse_entity_data(subsection))
            else:
                data = None
        else:
            if index != -1:
                if indices.index(index)+1 == len(indices):
                    subsection = self.header[index:]
                else:
                    subsection = self.header[index:indices[indices.index(index)+1]]
                data = self._parse_entity_data(subsection)
            else:
                data = None           
        
        return data
    
    def _parse_entity_data(self, section: str) -> dict:
        """
        Parses entity-related data and returns a dictionary of structured data
        """
        
        name = re.findall("COMPANY CONFORMED NAME:\t{3}(.+)", section)[0]
        name = name.strip()
        
        cik = int(re.findall("CENTRAL INDEX KEY:\t{3}([0-9]+)", section)[0])
        
        sic = re.findall("STANDARD INDUSTRIAL CLASSIFICATION:\t{1}([^\[0-9]+)\[([0-9]+)\]", section)
        if len(sic) == 0:
            sic_name, sic_code = None, None
        else:
            sic_name, sic_code = sic[0]
            sic_name = sic_name.strip()
            if sic_name == "":
                sic_name = None
            sic_code = int(sic_code)
        
        irs = re.findall("IRS NUMBER:\t{4}([0-9]+)", section)
        if len(irs) == 0:
            irs = None
        else:
            irs = int(irs[0])
        
        state = re.findall("STATE OF INCORPORATION:\t{3}([A-Z]{2})", section)
        if len(state) == 0:
            state = None
        else:
            state = state[0].strip()
        
        fiscal_year_end = re.findall("FISCAL YEAR END:\t{3}([0-9]{4})", section)
        if len(fiscal_year_end) == 0:
            fiscal_year_end = None
        else:
            year = dt.date.fromisoformat(self.date_filed).year
            month = int(fiscal_year_end[0][:2])
            day = int(fiscal_year_end[0][2:])
            fiscal_year_end = dt.date(
                year=year,
                month=month,
                day=day
            ).isoformat()
        
        business_address, mail_address = self._parse_addresses(section)
        
        if self.header.find("FORMER COMPANY:") == -1:
            former_names = None
        else:
            former_names = re.findall("FORMER CONFORMED NAME:\t(.+)\n\s+DATE OF NAME CHANGE:\t([0-9]{8})", section)
            former_names = [
                {
                    "name": item[0],
                    "date_of_change": dt.date(
                                        year=int(item[1][:4]),
                                        month=int(item[1][4:6]),
                                        day=int(item[1][6:8])
                                    ).isoformat()
                }
                for item in former_names
            ]
        
        data = {
            "name": name,
            "cik": cik,
            "sic": {
                "name": sic_name,
                "code": sic_code
            },
            "irs_number": irs,
            "state": state,
            "fiscal_year_end": fiscal_year_end,
            "business_address": business_address,
            "mail_address": mail_address,
            "former_names": former_names
        }
        
        return data
    
    def _parse_addresses(self, section) -> tuple:
        
        business_index = section.find("BUSINESS ADDRESS:")
        mail_index = section.find("MAIL ADDRESS:")
        
        if business_index == -1 and mail_index == -1:
            return None, None
        
        if business_index == -1:
            business_section = None
            mail_section = section[mail_index:]
        elif mail_index == -1:
            business_section = section[business_index:]
            mail_section = None
        elif business_index < mail_index:
            business_section = section[business_index:mail_index]
            mail_section = section[mail_index:]
        elif business_index > mail_index:
            business_section = section[business_section:]
            mail_section = section[mail_section:business_section]
        
        if business_section is None:
            business_address = None
        else:
            business_address = self._parse_single_address(business_section)
        
        if mail_section is None:
            mail_address = None
        else:
            mail_address = self._parse_single_address(mail_section)
            del mail_address["phone"]
        
        return business_address, mail_address
    
    def _parse_single_address(self, section) -> dict:
        if "STREET 1:" in section:
            street1 = re.findall("STREET 1:\t{2}(.+)", section)[0]
        else:
            street1 = None
        
        if "STREET 2:" in section:
            street2 = re.findall("STREET 2:\t{2}(.+)", section)[0]
        else:
            street2 = None
        
        if "CITY:" in section:
            city = re.findall("CITY:\t{3}(.+)", section)[0]
        else:
            city = None
        
        if "STATE:" in section:
            state = re.findall("STATE:\t{3}(.+)", section)[0]
        else:
            state = None
        
        if "ZIP:" in section:
            zip_ = re.findall("ZIP:\t{3}(.+)", section)
            try:
                zip_ = int(zip_[0])
            except ValueError:
                zip_ = None
        else:
            zip_ = None
        
        if "BUSINESS PHONE:" in section:
            phone = re.findall("BUSINESS PHONE:\t{2}(.+)", section)[0].upper()
        else:
            phone = None

        address = {
            "street1": street1,
            "street2": street2,
            "city": city,
            "state": state,
            "zip": zip_,
            "phone": phone
        }
        
        return address
    
    @property
    def accession_number(self) -> str:
        return self._accession_number
    
    @property
    def date_filed(self) -> str:
        return self._date_filed

    @property
    def date_of_change(self) -> str:
        return self._date_of_change
    
    @property
    def date_of_period(self) -> str:
        return self._date_of_period

    @property
    def document(self) -> str:
        return self._document

    @property
    def document_count(self) -> int:
        return self._document_count

    @property
    def effectiveness_date(self) -> str:
        return self._effectiveness_date
    
    @property
    def file(self) -> str:
        return self._file
    
    @property
    def file_number(self) -> str:
        return self._file_number
    
    @property
    def film_number(self) -> int:
        return self._film_number
    
    @property
    def header(self) -> str:
        return self._header

    @property
    def is_amendment(self) -> bool:
        return self._is_amendment

    @property
    def is_html(self) -> bool:
        return self._is_html
    
    @property
    def is_xml(self) -> bool:
        return self._is_xml

    @property
    def submission_type(self) -> str:
        return self._submission_type
    
    @classmethod
    def from_url(cls, url: str):
        file = requests.get(
            url=url,
            headers=HEADERS
        ).text
        
        if "<Message>The specified key does not exist.</Message>" in file:
            raise DatasetError(f"No filing exists for url '{url}'")
        return cls(file)


class Filing3(_SECFiling):
    pass


class Filing4(Filing3):
    pass


class Filing5(Filing4):
    pass


class Filing13G(_SECFiling):
    pass


class Filing13D(Filing13G):
    pass


class Filing13F(_SECFiling):
    def __init__(self, file: str):
        super().__init__(file)
        
        assert self.filer is not None
        self._parse_document()
    
    def _parse_document(self) -> None:
        if self.is_xml:
            self._soup = BeautifulSoup(self.document, "lxml")
            if self.is_amendment:
                amendment_type = self._soup.find("amendmenttype").text
                amendment_number = int(self._soup.find("amendmentno").text)
                self._amendment_information = {
                    "type": amendment_type,
                    "number": amendment_number
                }
            else:
                self._amendment_information = None
            self._report_type = self._soup.find("reporttype").text
            
            self._other_reporting_managers = []
            other_reporting_managers = self._soup.find("othermanagersinfo")
            if other_reporting_managers is not None:
                other_reporting_managers = other_reporting_managers.find_all("othermanager")
                for manager in other_reporting_managers:
                    name = manager.find("name").text
                    file_number = manager.find("form13ffilenumber")
                    if file_number is not None:
                        file_number = file_number.text
                    dct = {
                        "name": name,
                        "file_number": file_number
                    }
                    self._other_reporting_managers.append(dct)
            
            self._investments = self._parse_holdings_from_xml()
            self._other_managers = self._parse_other_managers_from_xml()
            self._signature = self._parse_signature_from_xml()
            self._summary = self._parse_summary_from_xml()
        else:
            raise NotImplementedError
    
    def _parse_other_managers_from_xml(self) -> dict:
        return
    
    def _parse_signature_from_xml(self) -> dict:
        signature = self._soup.find("signatureblock")
        
        name = signature.find("name").text
        title = signature.find("title").text
        phone = signature.find("phone").text
        city = signature.find("city").text
        state = signature.find("stateorcountry").text
        date = signature.find("signaturedate").text
        month, day, year = date.split("-")
        date = dt.date(year=int(year), month=int(month), day=int(day)).isoformat()
        
        return {
            "name": name,
            "title": title,
            "phone": phone,
            "city": city,
            "state": state,
            "date": date
        }
    
    def _parse_summary_from_xml(self) -> Union[dict, None]:
        if self.submission_type == "13F-NT":
            return None
        
        summary = self._soup.find("summarypage")
        number_of_investments = int(summary.find("tableentrytotal").text)
        portfolio_value = int(summary.find("tablevaluetotal").text) * 1000
        confidential_omitted = summary.find("isconfidentialomitted")
        if confidential_omitted is not None:
            confidential_omitted = confidential_omitted.text.lower()
            if confidential_omitted == "true":
                confidential_omitted = True
            elif confidential_omitted == "false":
                confidential_omitted = False
            else:
                raise ValueError("ambiguous confidential_ommitted bool")
        included_managers = {}
        managers = summary.find("othermanagers2info")
        if managers is None:
            included_managers = None
        else:
            managers = managers.find_all("othermanager2")
            for manager in managers:
                index = int(manager.find("sequencenumber").text)
                name = manager.find("name").text
                file_number = manager.find("form13ffilenumber")
                if file_number is not None:
                    file_number = file_number.text
                included_managers[index] = {
                    "name": name,
                    "file_number": file_number
                }
        
        return {
            "number_of_investments": number_of_investments,
            "portfolio_value": portfolio_value,
            "confidential_investments_omitted": confidential_omitted,
            "included_managers": included_managers
        }
    
    def _parse_holdings_from_xml(self) -> list:       
        if "n1:infoTable" in self._document:
            prefix = "n1:"
        elif "ns1:infoTable" in self._document:
            prefix = "ns1:"
        else:
            prefix = ""
        
        securities = []
        
        entries = self._soup.find_all(f"{prefix}infotable")
        for entry in entries:
            name = entry.find(f"{prefix}nameofissuer").text
            title = entry.find(f"{prefix}titleofclass").text
            cusip = entry.find(f"{prefix}cusip").text
            market_value = int(float(entry.find(f"{prefix}value").text)) * 1000
            amount = int(float(entry.find(f"{prefix}sshprnamt").text))
            amount_type = entry.find(f"{prefix}sshprnamttype").text
            quantity = {
                "amount": amount,
                "type": amount_type
            }
            option = entry.find(f"{prefix}putcall")
            if option is not None:
                option = option.text
            investment_discretion = entry.find(f"{prefix}investmentdiscretion").text
            included_managers = entry.find(f"{prefix}othermanager")
            if included_managers is not None:
                included_managers = included_managers.text.strip().upper()
                if included_managers in ("", "NONE"):
                    included_managers = None
                else:
                    included_managers = re.findall("([0-9]+)", included_managers)
                    included_managers = [int(index[0]) for index in included_managers]
            voting_authority = {
                "sole" : int(float(entry.find(f"{prefix}sole").text)),
                "shared": int(float(entry.find(f"{prefix}shared").text)),
                "none": int(float(entry.find(f"{prefix}none").text))
            }
        
            securities.append(
                {
                    "name": name,
                    "title": title,
                    "cusip": cusip,
                    "market_value": market_value,
                    "quantity": quantity,
                    "option": option,
                    "investment_discretion": investment_discretion,
                    "included_managers": included_managers,
                    "voting_authority": voting_authority
                }
            )
        
        return securities
        
    def _parse_holdings_from_text(self) -> dict:
        return
    
    def aggregate_portfolio(self, sorted_by=None) -> list:
        sort_variables = (
            None,
            "name",
            "title",
            "cusip",
            "market_value",
            "amount",
            "percentage",
            "investment_discretion"
        )
        if sorted_by not in (sort_variables):
            raise ValueError(f"sorting variable has to be in {sort_variables}")
            
        portfolio = {}
        for security in self.investments:
            name = security["name"]
            title = security["title"]
            cusip = security["cusip"]
            option = security["option"]
            if (name, title, cusip, option) in portfolio:
                portfolio[(name, title, cusip, option)]["market_value"] += security["market_value"]
                portfolio[(name, title, cusip, option)]["quantity"]["amount"] += security["quantity"]["amount"]
                portfolio[(name, title, cusip, option)]["voting_authority"]["sole"] += security["voting_authority"]["sole"]
                portfolio[(name, title, cusip, option)]["voting_authority"]["shared"] += security["voting_authority"]["shared"]
                portfolio[(name, title, cusip, option)]["voting_authority"]["none"] += security["voting_authority"]["none"]
            else:
                portfolio[(name, title, cusip, option)] = {
                    "market_value": security["market_value"],
                    "quantity": security["quantity"],
                    "investment_discretion": security["investment_discretion"],
                    "voting_authority": security["voting_authority"]
                }
        
        portfolio_value = sum([security["market_value"] for security in portfolio.values()])
        no_holdings = len(portfolio)
        
        portfolio = [
            {
                "name": name,
                "title": title,
                "cusip": cusip,
                "option": option,
                "percentage": round(float(values["market_value"] / portfolio_value), 4) if no_holdings != 1 else 1,
                "market_value": values["market_value"],
                "quantity": values["quantity"],
                "voting_authority": values["voting_authority"]
            }
            for (name, title, cusip, option), values in portfolio.items()
        ]
        
        desc = True if sorted_by in ("market_value", "amount", "percentage") else False
        
        if sorted_by is not None:
            if sorted_by == "amount":
                portfolio = sorted(portfolio, key=lambda x: x["quantity"][sorted_by], reverse=desc)
            else:
                portfolio = sorted(portfolio, key=lambda x: x[sorted_by], reverse=desc)
        
        return portfolio
    
    @property
    def amendment_information(self) -> dict:
        return self._amendment_information
    
    @property
    def filer(self) -> dict:
        return self._filer
    
    @property
    def investments(self) -> list:
        return self._investments
    
    @property
    def other_reporting_managers(self) -> list:
        return self._other_reporting_managers
    
    @property
    def report_type(self) -> str:
        return self._report_type

    @property
    def signature(self) -> dict:
        return self._signature

    @property
    def summary(self) -> dict:
        return self._summary


class FilingNPORT(_SECFiling):    
    _asset_types = {
        "AMBS": "Agency mortgage-backed securities",
        "ABS-APCP": "ABS-asset backed commercial paper",
        "ABS-CBDO": "ABS-collateralized bond/debt obligation",
        "ABS-MBS": "ABS-mortgage backed security",
        "ABS-O": "ABS-other",
        "ADR": "American Repository Receipt",
        "COMM": "Commodity",
        "DBT": "Debt",
        "DCO": "Derivative-commodity",
        "DCR": "Derivative-credit",
        "DE": "Derivative-equity",
        "DFE": "Derivative-foreign exchange",
        "DIR": "Derivative-interest rate",
        "DO": "Derivative-other",
        "EC": "Equity-common",
        "EDR": "Equity-Depositary Receipt",
        "EP": "Equity-preferred",
        "ETF": "Exchange Traded Fund",
        "GDR": "Global depositary receipt",
        "LON": "Loan",
        "RA": "Repurchase agreement",
        "RE": "Real estate",
        "SN": "Structured note",
        "STIV": "Short-term investment vehicle (e.g., money market fund, liquidity pool, or other cash management vehicle)",
        "UST": "U.S. Treasuries (including strips)"
    }
    
    _derivative_types = {
        "FWD": "Forward",
        "FUT": "Future",
        "OPT": "Option",
        "OTH": "Other",
        "SWO": "Swaption",
        "SWP": "Swap",
        "WAR": "Warrant"
    }
    
    _issuer_types = {
        "CORP": "Corporate",
        "MUN": "Municipal",
        "NUSS": "Non-U.S. sovereign",
        "PF": "Private fund",
        "RF": "Registered fund",
        "USGA": "U.S. government agency",
        "USGSE": "U.S. government sponsored entity",
        "UST": "U.S. Treasury"
    }

    _quantity_types = {
        "NC": "Number of contracts",
        "NS": "Number of shares",
        "OU": "Other units",
        "PA": "Principal amount"
    }
    
    def __init__(self, file: str) -> None:
        super().__init__(file)
        
        self._filer = self._filer[0]
        assert len(self.filer) != 0
        self._parse_document()

    def __repr__(self) -> str:
        return f"{self.submission_type} Filing({self.general_information['series']['cik']}|{self.general_information['series']['name']}|{self.general_information['reporting_date']})"

    def portfolio(self, sorted_by=None) -> list:
        sort_variables = (
            None,
            "name",
            "title",
            "market_value",
            "quantity",
            "percentage",
            "payoff_direction"
        )
        if sorted_by not in (sort_variables):
            raise ValueError(f"sorting variable has to be in {sort_variables}")
        
        if sorted_by is None:
            portfolio = self._investments
        else:
            desc = True if sorted_by in ("market_value", "quantity", "percentage") else False
            if sorted_by in ("quantity", "market_value", "percentage"):
                portfolio = sorted(self._investments, key=lambda x: x["amount"][sorted_by] if x["amount"][sorted_by] is not None else 0, reverse=desc)
            elif sorted_by == "name":
                portfolio = sorted(self._investments, key=lambda x: x["issuer"][sorted_by] if x["issuer"][sorted_by] is not None else "", reverse=desc)
            else:
                portfolio = sorted(self._investments, key=lambda x: x[sorted_by] if x[sorted_by] is not None else "", reverse=desc)
        
        return portfolio
    
    @property
    def filer(self) -> dict:
        return self._filer
    
    @property
    def has_short_positions(self) -> bool:
        return self._has_short_positions

    @property
    def explanatory_notes(self) -> dict:
        return self._explanatory_notes

    @property
    def general_information(self) -> dict:
        return self._general_information
    
    @property
    def fund_information(self) -> dict:
        return self._fund_information
    
    @property
    def flow_information(self) -> dict:
        return self.fund_information["flow_information"]
    
    @property
    def return_information(self) -> dict:
        return self.fund_information["return_information"]
    
    @property
    def securities_lending(self) -> dict:
        return self.fund_information["securities_lending"]

    @property
    def signature(self) -> dict:
        return self._signature

    def _parse_document(self) -> None:
        if self.is_xml:
            self._soup = BeautifulSoup(self.document, "lxml")
            self._general_information = self._parse_general_information()
            self._fund_information = self._parse_fund_information()
            self._investments = self._parse_investments()
            self._explanatory_notes = self._parse_explanatory_notes()
            self._signature = self._parse_signature()
        else:
            raise NotImplementedError("NPORT Filing classes can only be called on XML-compliant files")
        
        self._has_short_positions = True if any(item["amount"]["quantity"] < 0 for item in self._investments if item["amount"]["quantity"] is not None) else False
    
    def _parse_investments(self) -> list:
        entries = self._soup.find("invstorsecs").find_all("invstorsec")
        investments = []
        for entry in entries:
            issuer_name = entry.find("name").text
            if issuer_name == "N/A":
                issuer_name = None
            issuer_lei = entry.find("lei").text
            if issuer_lei == "N/A":
                issuer_lei = None
            issuer = {
                "name": issuer_name,
                "lei": issuer_lei
            }
            
            title = entry.find("title").text
            if title == "N/A":
                title = None

            identifier = {}
            cusip = entry.find("cusip").text
            if cusip != "N/A" and cusip != "0"*9:
                identifier["cusip"] = cusip
            other_identifier = entry.find("identifiers")
            isin = other_identifier.find("isin")
            if isin is not None:
                isin_value = isin.get("value")
                if isin_value is None:
                    isin_value = isin.text                
                identifier["isin"] = isin_value
            ticker = other_identifier.find("ticker")
            if ticker is not None:
                ticker_value = ticker.get("value")
                if ticker_value is None:
                    ticker_value = ticker.text                
                identifier["ticker"] = ticker_value
            other = other_identifier.find_all("other")
            for item in other:
                other_name = item.get("otherdesc")
                other_value = item.get("value")
                identifier[other_name] = other_value

            percentage = entry.find("pctval").text
            percentage = None if percentage == "N/A" else round(float(percentage) / 100, 6)
            market_value = float(entry.find("valusd").text)
            quantity = entry.find("balance").text
            quantity = None if quantity == "N/A" else float(quantity)
            quantity_type_abbr = entry.find("units").text
            if quantity_type_abbr == "N/A" or quantity_type_abbr is None:
                raise ValueError
            quantity_type = {"name": self._quantity_types[quantity_type_abbr], "abbreviation": quantity_type_abbr}
            
            currency = entry.find("curcd")
            if currency is None:
                currency = entry.find("currencyconditional")
                currency_name = currency.get("curcd")
                exchange_rate = currency.get("exchangert")
                exchange_rate = None if exchange_rate == "N/A" else round(float(exchange_rate), 6)
            else:
                currency_name = currency.text
                exchange_rate = None
            if currency_name == "N/A":
                currency_name = None
            currency = {
                "name": currency_name,
                "exchange_rate": exchange_rate
            }
            
            amount = {
                "percentage": percentage,
                "market_value": market_value,
                "quantity": quantity,
                "quantity_type": quantity_type,
                "currency": currency
            }
            
            payoff_direction = entry.find("payoffprofile").text
            if payoff_direction == "N/A":
                payoff_direction = None
            
            # asset and issuer type
            asset_type = entry.find("assetcat")
            if asset_type is not None:
                asset_type_abbr = asset_type.text
                asset_type = {"name": self._asset_types[asset_type_abbr], "abbreviation": asset_type_abbr}
            else:
                asset_type_name = entry.find("assetconditional").get("desc")
                asset_type = {"name": asset_type_name, "abbreviation": "OTH"}
            
            issuer_type = entry.find("issuercat")
            if issuer_type is None:
                issuer["type"] = {
                    "name": entry.find("issuerconditional").get("desc"),
                    "abbreviation": "OTH"
                }
            else:
                issuer["type"] = {
                    "name": self._issuer_types[issuer_type.text],
                    "abbreviation": issuer_type.text
                }
            country = entry.find("invcountry").text
            if country == "N/A":
                country = None
            issuer["country"] = country
            
            restricted_security = entry.find("isrestrictedsec").text
            if restricted_security == "Y":
                restricted_security = True
            elif restricted_security == "N":
                restricted_security = False
            assert isinstance(restricted_security, bool)
            
            liquidity_classification = None
            
            fair_value_level = entry.find("fairvallevel").text
            fair_value_level = None if fair_value_level == "N/A" else int(fair_value_level)
            
            debt_information = self._get_debt_information(entry)
            repurchase_information = None
            derivative_information = self._get_derivative_information(entry)
            securities_lending = self._get_lending_information(entry)
            
            investments.append(
                {
                    "issuer": issuer,
                    "title": title,
                    "identifier": identifier,
                    "amount": amount,
                    "payoff_direction": payoff_direction,
                    "asset_type": asset_type,
                    "restricted_security": restricted_security,
                    "liquidity_classification": liquidity_classification,
                    "us_gaap_fair_value_hierarchy": fair_value_level,
                    "debt_information": debt_information,
                    "repurchase_information": repurchase_information,
                    "derivative_information": derivative_information,
                    "securities_lending": securities_lending
                }
            )
        
        return investments
    
    def _get_debt_information(self, entry) -> Union[dict, None]:
        debt_section = entry.find("debtsec")
        if debt_section is None:
            return None
        
        maturity = debt_section.find("maturitydt").text
        coupon_type = debt_section.find("couponkind").text
        if coupon_type == "N/A" or coupon_type is None:
            raise ValueError
        coupon_rate = debt_section.find("annualizedrt").text
        coupon_rate = None if coupon_rate == "N/A" else float(coupon_rate) / 100

        in_default = debt_section.find("isdefault").text
        if in_default == "Y":
            in_default = True
        elif in_default == "N":
            in_default = False
        assert isinstance(in_default, bool)

        coupon_payments_deferred = debt_section.find("areintrstpmntsinarrs").text
        if coupon_payments_deferred == "Y":
            coupon_payments_deferred = True
        elif coupon_payments_deferred == "N":
            coupon_payments_deferred = False
        assert isinstance(coupon_payments_deferred, bool)

        paid_in_kind = debt_section.find("ispaidkind").text
        if paid_in_kind == "Y":
            paid_in_kind = True
        elif paid_in_kind == "N":
            paid_in_kind = False
        assert isinstance(paid_in_kind, bool)

        mandatory_convertible = debt_section.find("ismandatoryconvrtbl")
        if mandatory_convertible is None:
            convertible_information = None
        else:                
            mandatory_convertible = mandatory_convertible.text
            if mandatory_convertible == "Y":
                mandatory_convertible = True
            elif mandatory_convertible == "N":
                mandatory_convertible = False
            assert isinstance(mandatory_convertible, bool)

            contingent_convertible = debt_section.find("iscontngtconvrtbl").text
            if contingent_convertible == "Y":
                contingent_convertible = True
            elif contingent_convertible == "N":
                contingent_convertible = False
            assert isinstance(contingent_convertible, bool)

            conversion_asset_section = debt_section.find("dbtsecrefinstruments").find("dbtsecrefinstrument")
            conversion_asset_name = conversion_asset_section.find("name").text
            conversion_asset_title = conversion_asset_section.find("title").text
            conversion_asset_currency = conversion_asset_section.find("curcd").text
            conversion_asset_identifier = {}
            conversion_asset_cusip = conversion_asset_section.find("cusip")
            if conversion_asset_cusip is not None:
                conversion_asset_identifier["cusip"] = conversion_asset_cusip.get("value")
            conversion_asset_isin = conversion_asset_section.find("isin")
            if conversion_asset_isin is not None:
                conversion_asset_identifier["isin"] = conversion_asset_isin.get("value")
            other = conversion_asset_section.find_all("other")
            for item in other:
                other_name = item.get("otherdesc")
                other_value = item.get("value")
                conversion_asset_identifier[other_name] = other_value

            conversion_asset = {
                "name": conversion_asset_name,
                "title": conversion_asset_title,
                "currency": conversion_asset_currency,
                "identifier": conversion_asset_identifier
            }

            conversion_information = debt_section.find("currencyinfos").find("currencyinfo")
            conversion_ratio = conversion_information.get("convratio")
            conversion_ratio = None if conversion_ratio == "N/A" else float(conversion_ratio)                
            conversion_currency = conversion_information.get("curcd")
            conversion_information = {
                "ratio": conversion_ratio,
                "currency": conversion_currency
            }

            delta = debt_section.find("delta").text
            delta = None if delta == "XXXX" else float(delta)

            convertible_information = {
                "mandatory_convertible": mandatory_convertible,
                "contingent_convertible": contingent_convertible,
                "conversion_asset": conversion_asset,
                "conversion_ratio": conversion_information,
                "delta": delta
            }

        return {
            "maturity": maturity,
            "coupon": {
                "rate": coupon_rate,
                "type": coupon_type
            },
            "in_default": in_default,
            "coupon_payments_deferred": coupon_payments_deferred,
            "paid_in_kind": paid_in_kind,
            "convertible_information": convertible_information
        }
    
    def _get_derivative_information(self, entry) -> Union[dict, None]:
        derivative_section = entry.find("derivativeinfo")
        if derivative_section is None:
            return None

        counterparties = []
        counterparty_tags = derivative_section.find_all("counterparties")
        for counterparty in counterparty_tags:
            name = counterparty.find("counterpartyname").text
            if name == "N/A":
                name = None
            lei = counterparty.find("counterpartylei").text
            if lei == "N/A":
                lei = None
            counterparties.append({"name": name, "lei": lei})
        
        contents = derivative_section.contents
        if contents[0].text == "\n":
            abbr = contents[1].get("derivcat")
        else:
            abbr = contents[0].get("derivcat")

        if abbr == "OTH":
            name = derivative_section.contents[1].get("othdesc")
        else:
            name = self._derivative_types[abbr]

        if abbr == "FWD":
            information = self._parse_currency_forward_information(derivative_section)
        elif abbr == "FUT":
            information = self._parse_future_information(derivative_section)
        elif abbr in ("OPT", "SWO", "WAR"):
            information = self._parse_option_information(derivative_section)
        elif abbr == "SWP":
            information = self._parse_swap_information(derivative_section)
        elif abbr == "OTH":
            information = self._parse_other_derivative_information(derivative_section)
        
        return {
            "type": {
                "name": name,
                "abbreviation": abbr
            },
            "counterparties": counterparties,
            **information
        }

    def _parse_currency_forward_information(self, section) -> dict:
        amount_currency_sold = float(section.find("amtcursold").text)
        currency_sold = section.find("cursold").text
        if currency_sold == "N/A":
            currency_sold = None

        amount_currency_purchased = float(section.find("amtcurpur").text)
        currency_purchased = section.find("curpur").text
        if currency_purchased == "N/A":
            currency_purchased = None

        settlement_date = section.find("settlementdt").text

        unrealized_appreciation = section.find("unrealizedappr")
        if unrealized_appreciation is not None:
            unrealized_appreciation = float(unrealized_appreciation.text)

        return {
            "purchased": {
                "amount": amount_currency_purchased,
                "currency": currency_purchased
            },
            "sold": {
                "amount": amount_currency_sold,
                "currency": currency_sold
            },
            "settlement_date": settlement_date,
            "unrealized_appreciation": unrealized_appreciation
        }

    def _parse_future_information(self, section) -> dict:
        reference_section = section.find("descrefinstrmnt")
        reference_asset = self._parse_reference_asset_information(reference_section)

        trade_direction = section.find("payoffprof").text
        if trade_direction == "N/A":
            trade_direction = None

        expiration_date = section.find("expdate").text
        expiration_date = None if expiration_date == "N/A" else expiration_date

        notional_amount = section.find("notionalamt").text
        notional_amount = None if notional_amount == "N/A" else float(notional_amount)

        currency = section.find("curcd").text
        currency = None if currency == "N/A" else currency

        unrealized_appreciation = section.find("unrealizedappr")
        if unrealized_appreciation is not None:
            unrealized_appreciation = float(unrealized_appreciation.text)

        return {
            "reference_asset": reference_asset,
            "trade_direction": trade_direction,
            "expiration": expiration_date,
            "notional_amount": notional_amount,
            "currency": currency,
            "unrealized_appreciation": unrealized_appreciation
        }

    def _parse_option_information(self, section) -> dict:
        reference_section = section.find("descrefinstrmnt")
        reference_asset = self._parse_reference_asset_information(reference_section)

        type_ = section.find("putorcall").text
        trade_direction = section.find("writtenorpur").text

        no_shares = section.find("shareno")
        if no_shares is not None:
            no_shares = None if no_shares.text == "N/A" else float(no_shares.text)
            amount = {
                "quantity": no_shares,
                "quantity_type": {
                    "name": self._quantity_types["NS"],
                    "abbr": "NS"
                }
            }
        else:
            principal_amount = section.find("principalamt").text
            principal_amount = None if principal_amount == "N/A" else float(principal_amount)
            amount = {
                "quantity": principal_amount,
                "quantity_type": {
                    "name": self._quantity_types["PA"],
                    "abbr": "PA"
                },
            }

        exercise_price = float(section.find("exerciseprice").text)
        currency = section.find("exercisepricecurcd").text
        assert currency != "N/A"

        expiration_date = section.find("expdt").text
        assert expiration_date != "N/A"

        delta = section.find("delta").text
        delta = None if delta == "XXXX" else float(delta)

        unrealized_appreciation = float(section.find("unrealizedappr").text)

        return {
            "reference_asset": reference_asset,
            "type": type_,
            "trade_direction": trade_direction,
            "amount": amount,
            "exercise_data": {
                "price": exercise_price,
                "currency": currency
            },
            "expiration_date": expiration_date,
            "delta": delta,
            "unrealized_appreciation": unrealized_appreciation
        }

    def _parse_swap_information(self, derivative_section) -> dict:
        reference_section = derivative_section.find("descrefinstrmnt")
        if reference_section is None:
            pass
        else:
            reference_section = reference_section.find("otherrefinst")
            if reference_section is not None:
                reference_asset_name = reference_section.find("issuername").text
                if reference_asset_name == "N/A":
                    reference_asset_name = None
                reference_asset_title = reference_section.find("issuetitle").text
                identifier = {}
                identifier_section = reference_section.find("identifiers")
                cusip = identifier_section.find("cusip")
                if cusip is not None:
                    cusip = cusip.get("value")
                    identifier["cusip"] = cusip
                isin = identifier_section.find("isin")
                if isin is not None:
                    isin = isin.get("value")
                    identifier["isin"] = isin
                ticker = identifier_section.find("ticker")
                if ticker is not None:
                    ticker = ticker.get("value")
                    identifier["ticker"] = ticker
                other = identifier_section.find_all("other")
                for item in other:
                    other_name = item.get("otherdesc")
                    other_value = item.get("value")
                    identifier[other_name] = other_value
            else:
                reference_section = reference_section.find("indexbasketinfo")
                reference_asset_name = reference_section.find("indexname").text
                reference_asset_title = None
                identifier = {"isin": reference_section.find("indexidentifier").text}
            
        if derivative_section.find("floatingrecdesc") is not None:
            receiving_section = derivative_section.find("floatingrecdesc")
            receiving_currency = receiving_section.get("curcd")
            receiving_fixed_or_floating = receiving_section.get("fixedorfloating")
            receiving_index = receiving_section.get("floatingrtindex")
            receiving_spread = float(receiving_section.get("floatingrtspread"))
            receiving_amount = float(receiving_section.get("pmntamt"))
            receive_leg = {
                "currency": receiving_currency,
                "type": receiving_fixed_or_floating,
                "index": receiving_index,
                "spread": receiving_spread,
                "amount": receiving_amount
            }
        elif derivative_section.find("fixedrecdesc") is not None:
            receiving_section = derivative_section.find("fixedrecdesc")
            receiving_amount = float(receiving_section.get("amount"))
            receiving_currency = receiving_section.get("curcd")
            receiving_fixed_or_floating = receiving_section.get("fixedorfloating")
            receiving_rate = float(receiving_section.get("fixedrt"))
            receive_leg = {
                "amount": receiving_amount,
                "currency": receiving_currency,
                "type": receiving_fixed_or_floating,
                "rate": receiving_rate
            }
        elif derivative_section.find("otherrecdesc") is not None:
            receiving_section = derivative_section.find("otherrecdesc")
            receiving_fixed_or_floating = receiving_section.get("fixedorfloating")
            receiving_tenor = receiving_section.text
            receive_leg = {
                "type": receiving_fixed_or_floating,
                "tenor": receiving_tenor
            }

        if derivative_section.find("floatingpmntdesc") is not None:
            payment_section = derivative_section.find("floatingpmntdesc")
            payment_currency = payment_section.get("curcd")
            payment_fixed_or_floating = payment_section.get("fixedorfloating")
            payment_index = payment_section.get("floatingrtindex")
            payment_spread = float(payment_section.get("floatingrtspread"))
            payment_amount = float(payment_section.get("pmntamt"))
            pay_leg = {
                "currency": payment_currency,
                "type": payment_fixed_or_floating,
                "index": payment_index,
                "spread": payment_spread,
                "amount": payment_amount
            }
        elif derivative_section.find("fixedpmntdesc") is not None:
            payment_section = derivative_section.find("fixedpmntdesc")
            payment_amount = payment_section.get("amount")
            payment_amount = None if payment_amount == "N/A" else float(payment_amount)
            payment_currency = payment_section.get("curcd")
            assert payment_currency != "N/A"
            payment_fixed_or_floating = payment_section.get("fixedorfloating")
            payment_rate = float(payment_section.get("fixedrt"))
            pay_leg = {
                "amount": payment_amount,
                "currency": payment_currency,
                "type": payment_fixed_or_floating,
                "rate": payment_rate
            }
        elif derivative_section.find("otherpmntdesc") is not None:
            payment_section = derivative_section.find("otherpmntdesc")
            payment_fixed_or_floating = payment_section.get("fixedorfloating")
            payment_tenor = payment_section.text
            pay_leg = {
                "type": payment_fixed_or_floating,
                "tenor": payment_tenor
            }

        termination_date = derivative_section.find("terminationdt").text
        assert termination_date != "N/A"
        upfront_payments = float(derivative_section.find("upfrontpmnt").text)
        notional_amount = float(derivative_section.find("notionalamt").text)
        currency = derivative_section.find("curcd").text
        assert currency != "N/A"
        unrealized_appreciation = float(derivative_section.find("unrealizedappr").text)

        return {
            "reference_asset": {
                "name": reference_asset_name,
                "title": reference_asset_title,
                "identifier": identifier
            },
            "receive_leg": receive_leg,
            "pay_leg": pay_leg,
            "termination_date": termination_date,
            "upfront_payments": upfront_payments,
            "notional_amount": notional_amount,
            "currency": currency,
            "unrealized_appreciation": unrealized_appreciation
        }

    def _parse_other_derivative_information(self, derivative_section) -> dict:
        reference_section = derivative_section.find("descrefinstrmnt").find("otherrefinst")
        reference_asset_name = reference_section.find("issuername").text
        if reference_asset_name == "N/A":
            reference_asset_name = None
        reference_asset_title = reference_section.find("issuetitle").text
        identifier = {}
        identifier_section = reference_section.find("identifiers")
        cusip = identifier_section.find("cusip")
        if cusip is not None:
            cusip = cusip.get("value")               
            identifier["cusip"] = cusip
        isin = identifier_section.find("isin")
        if isin is not None:
            isin = isin.get("value")               
            identifier["isin"] = isin
        ticker = identifier_section.find("ticker")
        if ticker is not None:
            ticker = ticker.get("value")               
            identifier["ticker"] = ticker
        other = identifier_section.find_all("other")
        for item in other:
            other_name = item.get("otherdesc")
            other_value = item.get("value")
            identifier[other_name] = other_value

        termination_date = derivative_section.find("terminationdt").text
        assert termination_date != "N/A"
        notional_amounts = derivative_section.find("notionalamts")
        if notional_amounts is None:
            notional_amount = float(derivative_section.find("notionalamt").text)
        else:
            notional_amount = float(notional_amounts.find("notionalamt").get("amt"))
            notional_amount_currency = notional_amounts.find("notionalamt").get("curcd")
            notional_amount = {"amount": notional_amount, "currency": notional_amount_currency}

        delta = derivative_section.find("delta").text
        delta = None if delta == "XXXX" else float(delta)

        unrealized_appreciation = float(derivative_section.find("unrealizedappr").text)

        return {
            "reference_asset": {
                "name": reference_asset_name,
                "title": reference_asset_title,
                "identifier": identifier
            },
            "termination_date": termination_date,
            "notional_amount": notional_amount,
            "delta": delta,
            "unrealized_appreciation": unrealized_appreciation
        }
        
    def _get_lending_information(self, entry):
        security_lending_section = entry.find("securitylending")

        cash_collateral = security_lending_section.find("iscashcollateral")
        if cash_collateral is not None:
            assert cash_collateral.text == "N"
            cash_collateral = None
        else:
            assert security_lending_section.find("cashcollateralcondition").get("iscashcollateral") == "Y"
            cash_collateral = float(security_lending_section.find("cashcollateralcondition").get("cashcollateralval")) * 1000

        non_cash_collateral = security_lending_section.find("isnoncashcollateral")
        if non_cash_collateral is not None:
            assert non_cash_collateral.text == "N"
            non_cash_collateral = None
        else:
            assert security_lending_section.find("noncashcollateralcondition").get("isnoncashcollateral") == "Y"
            non_cash_collateral = float(security_lending_section.find("noncashcollateralcondition").get("noncashcollateralval")) * 1000

        loaned = security_lending_section.find("isloanbyfund")
        if loaned is not None:
            assert loaned.text == "N"
            loaned = None
        else:
            assert security_lending_section.find("loanbyfundcondition").get("isloanbyfund") == "Y"
            loaned = float(security_lending_section.find("loanbyfundcondition").get("loanval")) * 1000

        return {
            "cash_collateral": cash_collateral,
            "non_cash_collateral": non_cash_collateral,
            "loaned": loaned
        }
    
    def _parse_explanatory_notes(self) -> dict:
        note_section = self._soup.find("explntrnotes")
        if note_section is None:
            return None
        
        notes = {}
        note_tags = note_section.find_all("explntrnote")
        for tag in note_tags:
            note = tag.get("note").strip()
            item = tag.get("noteitem")
            notes[item] = note
        
        return notes
    
    def _parse_signature(self) -> dict:
        signature_section = self._soup.find("signature")
        prefix = "" if signature_section.find("ncom:datesigned") is None else "ncom:"
        
        date = signature_section.find(f"{prefix}datesigned").text
        company = signature_section.find(f"{prefix}nameofapplicant").text
        name = signature_section.find(f"{prefix}signername").text
        title = signature_section.find(f"{prefix}title").text
        signature = signature_section.find(f"{prefix}signature").text
        
        return {
            "date": date,
            "name": name,
            "title": title,
            "company": company,
            "signature": signature
        }
    
    def _parse_general_information(self) -> dict:
        form_data = self._soup.find("formdata")
        if form_data is None:
            form_data = self._soup.find("nport:formdata")
        
        general_info = form_data.find("geninfo")
        
        filer_lei = general_info.find("reglei").text
        fiscal_year_end = general_info.find("reppdend").text
        reporting_date = general_info.find("reppddate").text
        is_final_filing = general_info.find("isfinalfiling").text
        if is_final_filing == "Y":
            is_final_filing = True
        elif is_final_filing == "N":
            is_final_filing = False
        assert isinstance(is_final_filing, bool)

        # series data
        header_soup = BeautifulSoup(self._header, "lxml")
        series_section = header_soup.find("series-and-classes-contracts-data")
        
        if series_section is None:
            general_info = form_data.find("geninfo")
            series_cik = None
            series_name = general_info.find("seriesname").text
            lei = general_info.find("serieslei").text
            classes = None
        else:
            series_section = series_section.find("existing-series-and-classes-contracts").find("series")
            series_cik = series_section.find("series-id").find(text=True).strip()
            series_name = series_section.find("series-name").find(text=True).strip()
            lei = form_data.find("geninfo").find("serieslei").text

            # class data
            classes = []
            class_tags = series_section.find_all("class-contract")
            for tag in class_tags:
                cik = tag.find("class-contract-id").find(text=True).strip()
                name = tag.find("class-contract-name").find(text=True).strip()
                ticker = tag.find("class-contract-ticker-symbol")
                if ticker is not None:
                    ticker = ticker.find(text=True).strip()
                classes.append(
                    {
                        "cik": cik,
                        "name": name,
                        "ticker": ticker
                    }
                )
        
        series = {
            "name": series_name,
            "cik": series_cik,
            "lei": lei
        }
        
        return {
            "filer_lei": filer_lei,
            "series": series,
            "classes": classes,
            "fiscal_year_end": fiscal_year_end,
            "reporting_date": reporting_date,
            "is_final_filing": is_final_filing
        }
    
    def _parse_fund_information(self) -> dict:        
        form_data = self._soup.find("formdata")
        if form_data is None:
            form_data = self._soup.find("nport:formdata")

        fund_section = form_data.find("fundinfo")
        
        # assets and liabilities
        total_assets = float(fund_section.find("totassets").text)
        total_liabilities = float(fund_section.find("totliabs").text)
        net_assets = float(fund_section.find("netassets").text)
        
        # certain assets and liabilities
        miscellaneous_securities = float(fund_section.find("assetsattrmiscsec").text)
        assets_foreign_controlled_company = float(fund_section.find("assetsinvested").text)
        
        banks_1yr = float(fund_section.find("amtpayoneyrbanksborr").text)
        controlled_1yr = float(fund_section.find("amtpayoneyrctrldcomp").text)
        affiliates_1yr = float(fund_section.find("amtpayoneyrothaffil").text)
        other_1yr = float(fund_section.find("amtpayoneyrother").text)
        
        banks_longer = float(fund_section.find("amtpayaftoneyrbanksborr").text)
        controlled_longer = float(fund_section.find("amtpayaftoneyrctrldcomp").text)
        affiliates_longer = float(fund_section.find("amtpayaftoneyrothaffil").text)
        other_longer = float(fund_section.find("amtpayaftoneyrother").text)
        
        delayed_delivery = float(fund_section.find("delaydeliv").text)
        standby_commitment = float(fund_section.find("standbycommit").text)
        liquiditation_preference = float(fund_section.find("liquidpref").text)
        cash = fund_section.find("cshnotrptdincord")
        if cash is not None:
            cash = float(cash.text)

        accounts_payable = {
            "1-year": {
                "banks": banks_1yr,
                "controlled_companies": controlled_1yr,
                "other_affiliates": affiliates_1yr,
                "other": other_1yr
            },
            "long_term": {
                "banks": banks_longer,
                "controlled_companies": controlled_longer,
                "other_affiliates": affiliates_longer,
                "other": other_longer
            },
            "delayed_delivery": delayed_delivery,
            "standby_commitment": standby_commitment
        }
        
        certain_assets = {
            "miscellaneous_securities": miscellaneous_securities,
            "assets_foreign_controlled_company": assets_foreign_controlled_company,
            "accounts_payable": accounts_payable,
            "liquiditation_preference": liquiditation_preference,
            "cash": cash
        }
        
        # portfolio level risk information
        risk_section = fund_section.find("curmetrics")
        if risk_section is None:
            portfolio_level_risk = None
        else:
            portfolio_level_risk = {
                "interest_rate_risk": {},
                "credit_spread_risk": {}
            }

            for tag in risk_section.find_all("curmetric"):
                currency = tag.find("curcd").text
                duration_tag1 = tag.find("intrstrtriskdv01")
                duration_tag100 = tag.find("intrstrtriskdv100")
                portfolio_level_risk["interest_rate_risk"][currency] = {
                    "1bps": {
                        3: float(duration_tag1.get("period3mon")),
                        12: float(duration_tag1.get("period1yr")),
                        60: float(duration_tag1.get("period5yr")),
                        120: float(duration_tag1.get("period10yr")),
                        360: float(duration_tag1.get("period30yr"))
                    },
                    "100bps": {
                        3: float(duration_tag100.get("period3mon")),
                        12: float(duration_tag100.get("period1yr")),
                        60: float(duration_tag100.get("period5yr")),
                        120: float(duration_tag100.get("period10yr")),
                        360: float(duration_tag100.get("period30yr"))
                    }
                }

            investment_grade_tag = fund_section.find("creditsprdriskinvstgrade")
            non_investment_grade_tag = fund_section.find("creditsprdriskinvstgrade")
            portfolio_level_risk["credit_spread_risk"] = {
                "investment_grade": {
                    3: float(investment_grade_tag.get("period3mon")),
                    12: float(investment_grade_tag.get("period1yr")),
                    60: float(investment_grade_tag.get("period5yr")),
                    120: float(investment_grade_tag.get("period10yr")),
                    360: float(investment_grade_tag.get("period30yr"))
                },
                "non_investment_grade": {
                    3: float(non_investment_grade_tag.get("period3mon")),
                    12: float(non_investment_grade_tag.get("period1yr")),
                    60: float(non_investment_grade_tag.get("period5yr")),
                    120: float(non_investment_grade_tag.get("period10yr")),
                    360: float(non_investment_grade_tag.get("period30yr"))
                }
            }

        # lending information
        borrowers_tag = fund_section.find("borrowers")
        if borrowers_tag is None:
            borrowers = None
        else:
            borrowers = []
            for tag in borrowers_tag.find_all("borrower"):
                value = float(tag.get("aggrval"))
                lei = tag.get("lei")
                name = tag.get("name")
                borrowers.append(
                    {
                        "name": name,
                        "lei": lei,
                        "value": value
                    }
                )
        
        non_cash_collateral = fund_section.find("isnoncashcollateral")
        if non_cash_collateral is None or non_cash_collateral.text == "N":
            non_cash_collateral = None
        else:
            assert fund_section.find("aggregatecondition").get("isnoncashcollateral") == "Y"
            non_cash_collateral = []
            for tag in fund_section.find("aggregatecondition").find("aggregateinfos").find_all("aggregateinfo"):
                principal_amount = float(tag.get("amt"))
                collateral = float(tag.get("collatrl"))
                category_abbr = tag.find("invstcat").text
                asset_category = {
                    "name": self._asset_types[category_abbr],
                    "abbr": category_abbr
                }
                non_cash_collateral.append(
                    {
                        "principal_amount": principal_amount,
                        "collateral": collateral,
                        "asset_category": asset_category
                    }
                )

        securities_lending = {
            "borrowers": borrowers,
            "non_cash_collateral": non_cash_collateral
        }

        reporting_date = pd.to_datetime(self.general_information["reporting_date"])
        months = {
            1: (reporting_date - pd.DateOffset(months=2)).date().isoformat(),
            2: (reporting_date - pd.DateOffset(months=1)).date().isoformat(),
            3: reporting_date.date().isoformat()
        }

        # return information
        return_section = fund_section.find("returninfo")
        class_return_tags = return_section.find("monthlytotreturns").find_all("monthlytotreturn")
        class_returns = {}
        for tag in class_return_tags:
            class_id = tag.get("classid")
            class_returns[class_id] = {}
            for month in range(1, 4):
                return_ = tag.get(f"rtn{month}")
                return_ = None if return_ == "N/A" else round(float(return_) / 100, 4)
                class_returns[class_id][months[month]] = return_
        
        tag_contract_category_match = {
            "commoditycontracts": "Commodity Contracts",
            "creditcontracts": "Credit Contracts",
            "equitycontracts": "Equity Contracts",
            "foreignexchgcontracts": "Foreign Exchange Contracts",
            "interestrtcontracts": "Interest Rate Contracts",
            "othercontracts": "Other Contracts"
        }
        tag_derivative_instrument_match = {
            "forwardcategory": "Forward",
            "futurecategory": "Future",
            "optioncategory": "Option",
            "swapcategory": "Swap",
            "swaptioncategory": "Swaption",
            "warrantcategory": "Warrant",
            "othercategory": "Other"
        }
        
        derivative_gains = {}

        for contract in tag_contract_category_match.values():
            derivative_gains[contract] = {
                months[1]: None,
                months[2]: None,
                months[3]: None
            }
            for instrument in tag_derivative_instrument_match.values():
                derivative_gains[contract][instrument] = {
                    months[1]: None,
                    months[2]: None,
                    months[3]: None
                }

        derivative_return_tags = return_section.find("monthlyreturncats")
        if derivative_return_tags is not None:
            for contract_tag in derivative_return_tags.children:
                if contract_tag == "\n":
                    continue
                contract_name = tag_contract_category_match[contract_tag.name]
                derivative_gains[contract_name] = {}
                for instrument_tag in contract_tag.children:
                    if instrument_tag == "\n":
                        continue
                    elif instrument_tag.name in ("mon1", "mon2", "mon3"):
                        month = int(instrument_tag.name.replace("mon", ""))
                        realized_gain = instrument_tag.get("netrealizedgain")
                        realized_gain = None if realized_gain == "N/A" else float(realized_gain)
                        unrealized_appreciation = instrument_tag.get("netunrealizedappr")
                        unrealized_appreciation = None if unrealized_appreciation == "N/A" else float(unrealized_appreciation)
                        derivative_gains[contract_name][months[month]] = {
                            "realized_gain": realized_gain,
                            "unrealized_appreciation": unrealized_appreciation
                        }
                    else:
                        instrument_name = tag_derivative_instrument_match[instrument_tag.name]
                        derivative_gains[contract_name][instrument_name] = {}
                        for month in range(1, 4):
                            month_tag = instrument_tag.find(f"instrmon{month}")
                            realized_gain = month_tag.get("netrealizedgain")
                            realized_gain = None if realized_gain == "N/A" else float(realized_gain)
                            unrealized_appreciation = month_tag.get("netunrealizedappr")
                            unrealized_appreciation = None if unrealized_appreciation == "N/A" else float(unrealized_appreciation)
                            derivative_gains[contract_name][instrument_name][months[month]] = {
                                "realized_gain": realized_gain,
                                "unrealized_appreciation": unrealized_appreciation
                            }
        
        non_derivative_gains = {}
        for month in range(1,4):
            tag = return_section.find(f"othmon{month}")
            realized_gain = tag.get("netrealizedgain")
            realized_gain = None if realized_gain == "N/A" else float(realized_gain)
            unrealized_appreciation = tag.get("netunrealizedappr")
            unrealized_appreciation = None if unrealized_appreciation == "N/A" else float(unrealized_appreciation)
            non_derivative_gains[months[month]] = {
                "realized_gain": realized_gain,
                "unrealized_appreciation": unrealized_appreciation
            }
        
        return_information = {
            "class_returns": class_returns,
            "derivative_gains": derivative_gains,
            "non-derivative_gains": non_derivative_gains
        }

        # flow information
        flow_information = {}
        for month in range(1,4):
            flow = fund_section.find(f"mon{month}flow")
            redemptions = flow.get("redemption")
            redemptions = None if redemptions == "N/A" else float(redemptions)
            reinvestment = flow.get("reinvestment")
            reinvestment = None if reinvestment == "N/A" else float(reinvestment)
            sales = flow.get("sales")
            sales = None if sales == "N/A" else float(sales)
            flow_information[months[month]] = {
                "sales": sales,
                "reinvestments": reinvestment,
                "redemptions": redemptions
            }
        
        liquid_investment_minimum_information = None
        derivatives_transactions = None
        derivatives_exposure = None
        var_information = None

        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_assets": net_assets,
            "certain_assets": certain_assets,
            "portfolio_level_risk": portfolio_level_risk,
            "securities_lending": securities_lending,
            "return_information": return_information,
            "flow_information": flow_information,
            "liquid_investment_minimum_information": liquid_investment_minimum_information,
            "derivatives_transactions": derivatives_transactions,
            "derivatives_exposure": derivatives_exposure,
            "var_information": var_information
        }