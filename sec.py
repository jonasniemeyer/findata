import re
import numpy as np
import datetime as dt
from utils import _headers
from bs4 import BeautifulSoup
import pandas as pd
import requests

class SECFiling:
    def __init__(self, file: str) -> None:
        self._file = file
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
                filer["sic"] = self._parse_sic(item)
            except:
                filer["sic"] = None
            self._filer.append(filer)
        
        self._subject = []
        for item in self._subject_information:
            if len(item) == 0:
                continue
            subject = {}
            subject["name"] = self._parse_name(item)
            subject["cik"] = self._parse_cik(item)
            try:
                subject["sic"] = self._parse_sic(item)
            except:
                subject["sic"] = None
            self._subject.append(subject)
            
        self._form_type = self._parse_form_type()
        self._filing_date = self._parse_filing_date()
        
        self._is_html = True if "html" in self._file else False
    
    def _split_header(self):
        
        filer_section_start = self.header.find("FILER:")
        if filer_section_start == -1:
            filer_section_start = self.header.find("FILED BY:")   
        subject_section_start = self.header.find("SUBJECT COMPANY:")
        
        if subject_section_start > filer_section_start:
            raise ValueError("subject section comes after filer section")
        
        subject_section = self.header[subject_section_start:filer_section_start]   
        subject_section = subject_section.split("SUBJECT COMPANY:")
        
        filer_section = self.header[filer_section_start:]
        if self.header.find("FILER:") == -1:
            filer_section = filer_section.split("FILED BY:")[1:]
        else:
            filer_section = filer_section.split("FILER:")[1:]
        
        return subject_section, filer_section

    def _header_information(self) -> dict:
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
        sic = int(re.findall("STANDARD INDUSTRIAL CLASSIFICATION:\t{1}.+\[([0-9]+)\]", section)[0])
        return sic
    
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
        return self._header_information()

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
    def is_html(self):
        return self._is_html

    def __str__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        subject_names = [item["name"] for item in self.subject]
        if len(self.subject) == 0:
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
                f"Subject: {'/'.join(subject_names)})"
            )

    def __repr__(self) -> str:
        filer_names = [item["name"] for item in self.filer]
        subject_names = [item["name"] for item in self.subject]
        if len(self.subject) == 0:
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
                f"Subject: {'/'.join(subject_names)})"
            )
