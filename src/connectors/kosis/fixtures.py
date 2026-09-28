"""
Deterministic KOSIS Test Fixtures.
Provides authentic automotive industry production/shipment/inventory payloads.
"""
import json

KOSIS_AUTO_DT_1F02001_SAMPLE = json.dumps([
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T10",
        "ITM_NM": "생산지수",
        "PRD_DE": "202301",
        "DT": "108.4",
        "UNIT_NM": "2020=100"
    },
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T20",
        "ITM_NM": "출하지수",
        "PRD_DE": "202301",
        "DT": "105.1",
        "UNIT_NM": "2020=100"
    },
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T30",
        "ITM_NM": "재고지수",
        "PRD_DE": "202301",
        "DT": "92.3",
        "UNIT_NM": "2020=100"
    },
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T10",
        "ITM_NM": "생산지수",
        "PRD_DE": "202302",
        "DT": "112.7",
        "UNIT_NM": "2020=100"
    }
], ensure_ascii=False)

# Schema drift sample: ITM_ID T30 is missing, substituted by unexpected code
KOSIS_SCHEMA_DRIFT_SAMPLE = json.dumps([
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T10",
        "ITM_NM": "생산지수",
        "PRD_DE": "202301",
        "DT": "108.4",
        "UNIT_NM": "2020=100"
    },
    {
        "ORG_ID": "101",
        "TBL_ID": "DT_1F02001",
        "TBL_NM": "광업제조업동향조사(자동차 및 트레일러)",
        "ITM_ID": "T99_REVISED",
        "ITM_NM": "재고지수(개정)",
        "PRD_DE": "202301",
        "DT": "95.0",
        "UNIT_NM": "2020=100"
    }
], ensure_ascii=False)
