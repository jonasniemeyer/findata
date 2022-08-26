import requests
import re
import datetime as dt
from finance_data.utils import HEADERS, DatasetError
from typing import Union

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
    
    The document section holds the file-specific data (e.g. fund holdings in Form 13F filings)
    and parsing is solely governed by the respective subclass.
    
    Each SEC filing, irrespective of the type, has the following attributes:
        is_html: bool
        is_xml: bool
        
        file: str
        header: str
        document: str
        
        accession_number: str
        submission_type: str
        date_filed: str
        date_period: str
        
        filer: dict or None
        subject_company: dict or None
        reporting_owner: list or None
        issuer: dict or None
    """
    
    def __init__(self, file: str) -> None:
        self._file = file.replace("&nbsp;", " ")
        if "<SEC-HEADER>" in self.file:
            header_open, header_close = "<SEC-HEADER>", "</SEC-HEADER>"
        elif "<IMS-HEADER>" in self.file:
            header_open, header_close = "<IMS-HEADER>", "</IMS-HEADER>"
        self._header = self._file[self.file.find(header_open):self.file.find(header_close)] + header_close
        self._document = self.file[self.file.find("<DOCUMENT>"):self.file.find("</SEC-DOCUMENT>")]
        
        self._is_html = True if ("<html>" in self._file or "<HTML>" in self._file) else False
        self._is_xml = True if ("<xml>" in self._file or "<XML>" in self._file) else False
        
        self._parse_header()
        
    def _parse_header(self) -> None:
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
            zip_ = re.findall("ZIP:\t{3}(.+)", section)[0]
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
    def submission_type(self) -> str:
        return self._submission_type
    
    @property
    def is_amendment(self) -> bool:
        return self._is_amendment
    
    @property
    def document_count(self) -> int:
        return self._document_count
    
    @property
    def date_filed(self) -> str:
        return self._date_filed
    
    @property
    def date_of_period(self) -> str:
        return self._date_of_period
    
    @property
    def date_of_change(self) -> str:
        return self._date_of_change

    @property
    def effectiveness_date(self) -> str:
        return self._effectiveness_date
    
    @property
    def is_html(self) -> bool:
        return self._is_html
    
    @property
    def is_xml(self) -> bool:
        return self._is_xml
    
    @property
    def file(self) -> str:
        return self._file
    
    @property
    def header(self) -> str:
        return self._header
    
    @property
    def document(self) -> str:
        return self._document
    
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
    pass

class FilingNPORT(_SECFiling):
    pass