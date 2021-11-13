import re
import numpy as np
import datetime as dt
from finance_data.utils import _headers
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
import requests

class _SECFiling:
    def __init__(self, file: str) -> None:
        self._file = file.replace("&nbsp;", " ")
        self._header = self._file[:self._file.find("</SEC-HEADER>")]
        self._document = self._file[self._file.find("<DOCUMENT>"):]
        self._subject_information, self._filer_information = self._split_header()
        
        self._filer = []
        for item in self._filer_information:
            if len(item) == 0:
                continue
            filer = {}
            filer["name"] = self._parse_name(item)
            filer["cik"] = self._parse_cik(item)
            try:
                filer["sic_name"], filer["sic_code"] = self._parse_sic(item)
            except:
                filer["sic_name"], filer["sic_code"] = None, None
            self._filer.append(filer)
        
        self._subject = {}
            
        self._form_type = self._parse_form_type()
        self._filing_date = self._parse_filing_date()
        try:
            self._period_date = self._parse_period_date()
        except:
            self._period_date = self._filing_date
        self._header_information = self._get_header_information()
        self._is_html = True if ("<html>" in self._document or "<HTML>" in self._document) else False
        self._is_xml = True if ("<xml>" in self._document or "<XML>" in self._document) else False
    
    def _split_header(self):
        
        filer_section_start = self.header.find("FILER:")
        if filer_section_start == -1:
            filer_section_start = self.header.find("FILED BY:")
            
        subject_section_start = self.header.find("SUBJECT COMPANY:")
        
        if subject_section_start > filer_section_start:
            subject_section = self.header[subject_section_start:]
            filer_section = self.header[filer_section_start:subject_section_start]
        else:
            subject_section = self.header[subject_section_start:filer_section_start]
            filer_section = self.header[filer_section_start:]
        
        if self.header.find("FILER:") == -1:
            filer_section = filer_section.split("FILED BY:")[1:]
        else:
            filer_section = filer_section.split("FILER:")[1:]
        return subject_section, filer_section

    def _get_header_information(self) -> dict:
        self.company_information = {}
        self.company_information["filer"] = self.filer
        self.company_information["subject"] = self.subject
        self.company_information["form_type"], self.company_information["amendment"] = self.form_type
        self.company_information["filing_date"] = self.filing_date
        return self.company_information

    def _parse_name(self, section) -> str:
        name = re.findall("COMPANY CONFORMED NAME:\t{3}(.+)", section)[0]
        name = name.strip().lower().title()
        return name

    def _parse_cik(self, section) -> int:
        cik = int(re.findall("CENTRAL INDEX KEY:\t{3}([0-9]+)", section)[0])
        return cik
    
    def _parse_sic(self, section) -> int:
        sic_name, sic_code = re.findall("STANDARD INDUSTRIAL CLASSIFICATION:\t{1}(.+)\[([0-9]+)", section)[0]
        sic_name = sic_name.strip().lower().title()
        sic_code = int(sic_code)
        return sic_name, sic_code
    
    def _parse_form_type(self) -> tuple:
        form = re.findall("FORM TYPE:\t{2}(.+)\n", self._file)[0]
        amendment = True if form.endswith("/A") else False
        return form, amendment

    def _parse_filing_date(self) -> str:
        date = re.findall("FILED AS OF DATE:\t{2}([0-9]+)", self._file)[0]
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
        date = dt.date(year, month, day).isoformat()
        return date

    def _parse_period_date(self) -> str:
        date = re.findall("CONFORMED PERIOD OF REPORT:\t([0-9]+)", self._file)[0]
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
        date = dt.date(year, month, day).isoformat()
        return date

    @classmethod
    def from_url(cls, url: str):
        txt = requests.get(
            url = url,
            headers = _headers
        ).text
        return cls(txt)
    
    @property
    def file(self) -> str:
        return self._file
    
    @property
    def header(self) -> str:
        return self._header
    
    @property
    def document(self) -> str:
        return self._document
    
    @property
    def header_information(self):
        return self._header_information

    @property
    def filer(self) -> dict:
        return self._filer
    
    @property
    def subject(self) -> dict:
        return self._subject

    @property
    def form_type(self) -> str:
        return self._form_type

    @property
    def filing_date(self) -> str:
        return self._filing_date

    @property
    def period_date(self) -> str:
        return self._period_date
    
    @property
    def is_html(self):
        return self._is_html
    
    @property
    def is_xml(self):
        return self._is_xml

    def __str__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        if not self.subject:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)})"
                )
        else:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)}; "
                f"Subject: {self.subject['name']})"
            )

    def __repr__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        if not self.subject:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)})"
                )
        else:
            return (
                f"{self.form_type[0]} Filing"   
                f"(Date: {self.filing_date}; "
                f"Filer: {'/'.join(filer_names)}; "
                f"Subject: {self.subject['name']})"
            )


class Filing13D(_SECFiling):
    def __init__(self, file: str) -> None:
        super().__init__(file)
        self._subject["name"] = self._parse_name(self._subject_information)
        self._subject["cik"] = self._parse_cik(self._subject_information)
        self._subject["cusip"] = self._parse_cusip()
        try:
            self._subject["sic_name"], self._subject["sic_code"] = self._parse_sic(self._subject_information)
        except:
            self._subject["sic_name"], self._subject["sic_code"] = None, None
    
    def _parse_cusip(self) -> str:
        soup = BeautifulSoup(self.document, "lxml")
        document_flat = " ".join(soup.get_text().replace("\xa0", " ").split())
        cusips = re.findall(
            "(?i)([0-9A-Z]{1}[0-9]{2}[- ]*[0-9][0-9A-Za-z][- ]*[0-9A-Za-z][- ]*[0-9]{0,2}[- ]*[0-9]{0,1})[\s\-_]*\(CUSIP Number\)", document_flat
        )
        if len(cusips) == 0:
            cusips = re.findall(
                "(?i)Cusip (?:No|Number)\s{0,1}(?:\:|\.)\s*([0-9A-Z]{1}[0-9]{2}[- ]*[0-9][0-9A-Za-z][- ]*[0-9A-Za-z][- ]*[0-9]{0,2}[- ]*[0-9]{0,1})", document_flat
            )
        cusips = [item.strip().replace(" ", "").replace("-", "") for item in cusips]
        counter = Counter(cusips)
        return counter.most_common(1)[0][0]

    def _parse_percent_acquired(self) -> float:
        soup = BeautifulSoup(self.document, "lxml")
        document_flat = " ".join(soup.get_text().replace("\xa0", " ").split())
        percentage = re.findall("(?i)PERCENT(?:AGE|)\s*OF\s*CLASS\s*REPRESENTED\s*BY\s+AMOUNT\s*IN\s*ROW.*?\s*([0-9.,]+)\s?%", document_flat)[0]
        percentage = round(float(percentage) / 100, 8)
        return percentage

    def _parse_shares_acquired(self) -> int:
        soup = BeautifulSoup(self.document, "lxml")
        document_flat = " ".join(soup.get_text().replace("\xa0", " ").split())
        shares = re.findall("(?i)(?:AGGREGATE|)\s*AMOUNT\s+(?:BENEFICIALLY|)\s*OWNED\s*BY\s*(?:EACH|)\s*(?:REPORTING|)\s*PERSON.*?\s*([0-9]+?,?[0-9,]+)", document_flat)[0]
        shares = int(shares.replace(",", ""))
        return shares
    
    @property
    def subject_cusip(self) -> str:
        return self.subject["cusip"]
    
    @property
    def percent_acquired(self) -> float:
        if not hasattr(self, "_percent_acquired"):
            self._percent_acquired = self._parse_percent_acquired()
        return self._percent_acquired
    
    @property
    def shares_acquired(self) -> int:
        if not hasattr(self, "_shares_acquired"):
            self._shares_acquired = self._parse_shares_acquired()
        return self._shares_acquired


class Filing13G(Filing13D):
    def __init__(self, file: str) -> None:
        super().__init__(file)


class Filing13F(_SECFiling):
    def __init__(self, file):
        super().__init__(file)

    @property
    def holdings(self) -> float:
        if not hasattr(self, "_holdings"):
            self._holdings = self._parse_holdings()
        return self._holdings

    def _parse_holdings(self, ordered="percentage") -> dict:
        if self.is_xml:
            securities = self._get_holdings_xml()
        else:
            securities = self._get_holdings_text()
        
        holdings = {'holdings': []}
        for (name, title, cusip, option), (market_value, no_shares) in securities.items():
            security = {}
            security['name'] = name
            security['title'] = title
            security["cusip"] = cusip
            security["percentage"] = None
            security['market_value'] = market_value * 1000
            security['no_shares'] = int(no_shares)
            security['option'] = option
            holdings["holdings"].append(security)
        
        #some filers report market value not in thousands
        prices = [item["market_value"] / item["no_shares"] for item in holdings["holdings"]]
        if len(prices) > 0:
            if [item > 1000 for item in prices].count(True) / len(prices) > 0.5:
                for holding in holdings["holdings"]:
                    holding["market_value"] /= 1000
        
        holdings['no_holdings'] = len(holdings['holdings'])
        holdings['portfolio_value'] = sum([value['market_value'] for value in holdings['holdings']])

        for item in holdings['holdings']:
            item["percentage"] = item["market_value"] / holdings['portfolio_value']

        if ordered not in (None, "name", "title", "cusip", "market_value", "no_shares", "percentage"):
            raise ValueError('ordered argument must be in (None, "name", "title", "cusip", "market_value", "no_shares", "percentage")')

        if ordered is not None:
            if ordered in ("name", "title", "cusip"):
                holdings['holdings'] = sorted(holdings['holdings'], key = lambda item: item[ordered])
            else:
                holdings['holdings'] = sorted(holdings['holdings'], key = lambda item: item[ordered], reverse = True)
        
        return holdings

    def _get_holdings_xml(self) -> dict:
        holdings = {}
        soup = BeautifulSoup(self._document, "lxml")
        if "ns1:infoTable" in self._document:
            prefix = "ns1:"
        else:
            prefix = ""
        entries = soup.find_all(f"{prefix}infotable")
        for entry in entries:
            name = entry.find(f"{prefix}nameofissuer").text
            title = entry.find(f"{prefix}titleofclass").text
            cusip = entry.find(f"{prefix}cusip").text
            no_shares = entry.find(f"{prefix}sshprnamt").text
            market_value = entry.find(f"{prefix}value").text
            try:
                option = entry.find(f"{prefix}putcall").text
            except:
                option = ""
            if any(item in ("0", "") for item in (no_shares, market_value, cusip)) or len(cusip) != 9:
                    pass
            no_shares = float(no_shares.replace(",",""))
            market_value = float(market_value.replace(",",""))
            holdings[(name, title, cusip, option)] = holdings.get((name, title, cusip, option), np.array([0, 0])) + np.array([market_value, no_shares])
        return holdings

    def _get_holdings_text(self) -> dict:
        holdings = {}
        table = self.document.replace("\n", "   ")
        items = re.findall(
            "(?i)([A-Z]\S+(?:[ ]\S+?[A-Z]\S+)*)"
            "(?:[\s\"]+?)"
            "(\S*?(?:[ ]\S+)*?)?"
            "(?:[\s\"]*)"
            "([0-9A-Z]{4}[0-9A-Z]{2}[- ]*[0-9]{2}[- ]*?[0-9]?)\.?"
            "(?:[\s\"]+?)"
            "(?:\$[ ]*|)([0-9]+(?:[0-9]|,[0-9]{3}|\.[0-9]{1,3})*)\.?"
            "(?:[\s\"]+?)"
            "([0-9]{1,3}(?:[0-9]|,[0-9]{3}|\.[0-9]{1,3})*)[x\.]?"
            "(?:[\s\"]*)"
            "(SH|PRN|X|SHRS|)"
            "\s*?"
            "(CALL|PUT|)",
            table
        )
        for item in items:
            name, title, cusip, market_value, no_shares, _type, option = item
            name = name.replace("\n", "").strip()
            cusip = cusip.replace(" ", "").replace("-", "")
            no_shares = self._convert_number(no_shares)
            market_value = self._convert_number(market_value)
            if any(item in ("0", "") for item in (no_shares, market_value, cusip)) or len(cusip) not in (8,9):
                continue
            option = option.strip()
            if "CALL" in _type:
                option = "CALL"
            elif "PUT" in _type:
                option ="PUT"
            else:
                option = ""
            holdings[(name, title, cusip, option)] = holdings.get((name, title, cusip, option), np.array([0, 0])) + np.array([market_value, no_shares])
        return holdings

    def _convert_number(self, value: str) -> float:
        if "(" in value and ")" in value:
            value = float(value.replace(",","").replace("(", "").replace(")", "")) * (-1)
        else:
            value = float(value.replace(",",""))
        return value