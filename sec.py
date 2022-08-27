import requests
import re
import datetime as dt
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
            "cik": item[0],
            "ticker": item[3],
            "series_identifier": item[1],
            "class_identifier": item[2],
        }
        for item in items
    ]
    return items


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
            fiscal_year_end = (int(fiscal_year_end[0][:2]), int(fiscal_year_end[0][2:]))
        
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
            "sic_name": sic_name,
            "sic_code": sic_code,
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
            phone = re.findall("BUSINESS PHONE:\t{2}(.+)", section)[0]
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
        self._soup = BeautifulSoup(self._document, "lxml")

        if self.is_xml:
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
            market_value = int(entry.find(f"{prefix}value").text) * 1000
            amount = int(float(entry.find(f"{prefix}sshprnamt").text))
            security_type = entry.find(f"{prefix}sshprnamttype").text
            quantity = {
                "amount": amount,
                "type": security_type
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
    pass