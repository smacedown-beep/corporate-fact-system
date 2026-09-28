"""
Deterministic ECOS Test Fixtures.
Provides authentic Bank of Korea USD/KRW exchange rate and interest rate payloads.
"""
import json

ECOS_USDKRW_036Y001_SAMPLE = json.dumps({
    "StatisticSearch": {
        "list_total_count": 3,
        "row": [
            {
                "STAT_CODE": "036Y001",
                "STAT_NAME": "주요국 통화의 대원화 환율",
                "ITEM_CODE1": "0000001",
                "ITEM_NAME1": "원/미국달러(매매기준율)",
                "ITEM_CODE2": None,
                "ITEM_NAME2": None,
                "ITEM_CODE3": None,
                "ITEM_NAME3": None,
                "ITEM_CODE4": None,
                "ITEM_NAME4": None,
                "UNIT_NAME": "원",
                "TIME": "20230102",
                "DATA_VALUE": "1,272.0"
            },
            {
                "STAT_CODE": "036Y001",
                "STAT_NAME": "주요국 통화의 대원화 환율",
                "ITEM_CODE1": "0000001",
                "ITEM_NAME1": "원/미국달러(매매기준율)",
                "ITEM_CODE2": None,
                "ITEM_NAME2": None,
                "ITEM_CODE3": None,
                "ITEM_NAME3": None,
                "ITEM_CODE4": None,
                "ITEM_NAME4": None,
                "UNIT_NAME": "원",
                "TIME": "20230103",
                "DATA_VALUE": "1,279.0"
            },
            {
                "STAT_CODE": "036Y001",
                "STAT_NAME": "주요국 통화의 대원화 환율",
                "ITEM_CODE1": "0000001",
                "ITEM_NAME1": "원/미국달러(매매기준율)",
                "ITEM_CODE2": None,
                "ITEM_NAME2": None,
                "ITEM_CODE3": None,
                "ITEM_NAME3": None,
                "ITEM_CODE4": None,
                "ITEM_NAME4": None,
                "UNIT_NAME": "원",
                "TIME": "20230104",
                "DATA_VALUE": "1,271.0"
            }
        ]
    }
}, ensure_ascii=False)

ECOS_BASE_RATE_060Y001_SAMPLE = json.dumps({
    "StatisticSearch": {
        "list_total_count": 1,
        "row": [
            {
                "STAT_CODE": "060Y001",
                "STAT_NAME": "한국은행 기준금리 및 여수신금리",
                "ITEM_CODE1": "0101000",
                "ITEM_NAME1": "한국은행 기준금리",
                "UNIT_NAME": "연%",
                "TIME": "20230113",
                "DATA_VALUE": "3.50"
            }
        ]
    }
}, ensure_ascii=False)

ECOS_ERROR_INVALID_KEY_SAMPLE = json.dumps({
    "RESULT": {
        "CODE": "ERROR-300",
        "MESSAGE": "인증키가 유효하지 않습니다."
    }
}, ensure_ascii=False)
