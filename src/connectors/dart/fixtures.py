"""
Known Forensic Test Fixtures and Synthetic DART ZIP Generators.
Provides deterministic fixtures matching historical forensic cases.
"""
import io
import zipfile
from typing import Dict, Any


def create_synthetic_dart_zip(
    corp_code: str,
    corp_name: str,
    stock_code: str,
    rcept_no: str,
    report_name: str,
    additional_xml_body: str = ""
) -> bytes:
    """
    Creates a cryptographically valid ZIP archive containing an official-structure document.xml.
    """
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<DOCUMENT>
    <HEADER>
        <CORP_CODE>{corp_code}</CORP_CODE>
        <CORP_NAME>{corp_name}</CORP_NAME>
        <STOCK_CODE>{stock_code}</STOCK_CODE>
        <RCEPT_NO>{rcept_no}</RCEPT_NO>
        <REPORT_NAME>{report_name}</REPORT_NAME>
    </HEADER>
    <BODY>
        {additional_xml_body}
    </BODY>
</DOCUMENT>
"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("document.xml", xml_content.encode("utf-8"))
    return buf.getvalue()


# Known Case 1: TLI 2023Q3 (Erroneously treated as HMC in legacy project)
TLI_2023_Q3_METADATA = {
    "corp_code": "00261887",
    "corp_name": "주식회사 티엘아이",
    "company_name": "주식회사 티엘아이",
    "stock_code": "062970",
    "rcept_no": "20231114002693",
    "report_name": "분기보고서 (2023.09)",
    "report_period": "2023.09",
    "filing_date": "2023-11-14"
}

# Known Case 2: Authentic HMC 2023Q3
HMC_2023_Q3_METADATA = {
    "corp_code": "00164742",
    "corp_name": "현대자동차",
    "company_name": "현대자동차",
    "stock_code": "005380",
    "rcept_no": "20231114002201",
    "report_name": "분기보고서 (2023.09)",
    "report_period": "2023.09",
    "filing_date": "2023-11-14"
}

# Known Case 3: Authentic HMC 2023Q1 with official EPS Note 30
HMC_2023_Q1_EPS_XML_BODY = """
<SECTION title="30. 주당이익">
    <TABLE id="eps_table">
        <ROW id="numerator_row">
            <CELL col="item">지배기업 소유주지분 순이익</CELL>
            <CELL col="amount" unit="KRW">2564055000000</CELL>
        </ROW>
        <ROW id="shares_row">
            <CELL col="item">기본주당이익 산정용 가중평균보통주식수</CELL>
            <CELL col="shares" unit="주">202463266</CELL>
        </ROW>
        <ROW id="basic_eps_row">
            <CELL col="item">기본주당순이익</CELL>
            <CELL col="eps" unit="KRW">12664</CELL>
        </ROW>
    </TABLE>
</SECTION>
"""

HMC_2023_Q1_METADATA = {
    "corp_code": "00164742",
    "corp_name": "현대자동차",
    "company_name": "현대자동차",
    "stock_code": "005380",
    "rcept_no": "20230515002403",
    "report_name": "분기보고서 (2023.03)",
    "report_period": "2023.03",
    "filing_date": "2023-05-15",
    "expected_numerator": 2564055000000,
    "expected_shares": 202463266,
    "expected_eps": 12664
}
