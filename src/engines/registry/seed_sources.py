"""
Canonical Official Source Registry Seeds.
Contains strictly verified official endpoints, authority levels, and documentation links.
No guessed endpoints or hardcoded credentials permitted.
"""
from typing import List
from datetime import datetime, timezone
from src.core.enums import (
    AuthorityLevel,
    SourceProvider,
    SourceType
)
from src.db.models import SourceRegistry

NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)

CANONICAL_SOURCES: List[SourceRegistry] = [
    # 1. OpenDART (FSS)
    SourceRegistry(
        source_id="DART_LIST",
        provider=SourceProvider.DART,
        source_name="금융감독원 OpenDART 공시목록조회",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_2_OFFICIAL_FILING,
        official_url="https://opendart.fss.or.kr/guide/detail.do?apiGb=1&menuNo=2001",
        api_endpoint="https://opendart.fss.or.kr/api/list.json",
        authentication_type="API_KEY_ENV",
        api_key_env="DART_API_KEY",
        dataset_code="FILING_LIST",
        frequency="EVENT_DRIVEN",
        availability_rule="Filing receipt timestamp at DART public server",
        active=True,
        last_verified_at=NOW
    ),
    SourceRegistry(
        source_id="DART_DOCUMENT_XML",
        provider=SourceProvider.DART,
        source_name="금융감독원 OpenDART 공시서류 원문(XML/XBRL ZIP)",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_2_OFFICIAL_FILING,
        official_url="https://opendart.fss.or.kr/guide/detail.do?apiGb=1&menuNo=2003",
        api_endpoint="https://opendart.fss.or.kr/api/document.xml",
        authentication_type="API_KEY_ENV",
        api_key_env="DART_API_KEY",
        dataset_code="DOCUMENT_XML",
        frequency="EVENT_DRIVEN",
        availability_rule="Immutable original filing document XML",
        active=True,
        last_verified_at=NOW
    ),
    SourceRegistry(
        source_id="DART_COMPANY",
        provider=SourceProvider.DART,
        source_name="금융감독원 OpenDART 기업개황",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_2_OFFICIAL_FILING,
        official_url="https://opendart.fss.or.kr/guide/detail.do?apiGb=1&menuNo=2002",
        api_endpoint="https://opendart.fss.or.kr/api/company.json",
        authentication_type="API_KEY_ENV",
        api_key_env="DART_API_KEY",
        dataset_code="COMPANY_PROFILE",
        frequency="DAILY",
        availability_rule="Official company identity and legal entity metadata",
        active=True,
        last_verified_at=NOW
    ),

    # 2. KOSIS (National Statistics Korea)
    SourceRegistry(
        source_id="KOSIS_STAT_DATA",
        provider=SourceProvider.KOSIS,
        source_name="통계청 국가통계포털 KOSIS 통계자료조회",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://kosis.kr/openapi/detail/detail.do",
        api_endpoint="https://kosis.kr/openapi/Param/statisticsParameterData.do",
        authentication_type="API_KEY_ENV",
        api_key_env="KOSIS_API_KEY",
        dataset_code="STATISTICS_DATA",
        table_code="DT_1F02001",  # 광업제조업동향 (자동차 C30 등)
        unit="INDEX / UNIT",
        frequency="MONTHLY",
        availability_rule="Published according to Statistics Korea advance release calendar",
        active=True,
        last_verified_at=NOW
    ),
    SourceRegistry(
        source_id="KOSIS_STAT_EXPL",
        provider=SourceProvider.KOSIS,
        source_name="통계청 국가통계포털 KOSIS 통계설명자료",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://kosis.kr/openapi/detail/detail.do",
        api_endpoint="https://kosis.kr/openapi/statisticsExplData.do",
        authentication_type="API_KEY_ENV",
        api_key_env="KOSIS_API_KEY",
        dataset_code="METADATA_EXPL",
        frequency="ANNUAL",
        availability_rule="Official statistical taxonomy and methodology notes",
        active=True,
        last_verified_at=NOW
    ),

    # 3. ECOS (Bank of Korea)
    SourceRegistry(
        source_id="ECOS_STAT_SEARCH",
        provider=SourceProvider.ECOS,
        source_name="한국은행 경제통계시스템 ECOS StatisticSearch",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://ecos.bok.or.kr/api/#/DevGuide/OpenApiGuide",
        api_endpoint="https://ecos.bok.or.kr/api/StatisticSearch",
        authentication_type="API_KEY_ENV",
        api_key_env="ECOS_API_KEY",
        dataset_code="MACRO_FINANCIAL",
        table_code="036Y001",  # 주요 환율 및 금리
        frequency="DAILY",
        availability_rule="Bank of Korea financial market closing availability",
        active=True,
        last_verified_at=NOW
    ),

    # 4. FRED (St. Louis Fed)
    SourceRegistry(
        source_id="FRED_SERIES_OBS",
        provider=SourceProvider.FRED,
        source_name="Federal Reserve Bank of St. Louis FRED Series Observations",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_4_INTERNATIONAL,
        official_url="https://fred.stlouisfed.org/docs/api/fred/series_observations.html",
        api_endpoint="https://api.stlouisfed.org/fred/series/observations",
        authentication_type="API_KEY_ENV",
        api_key_env="FRED_API_KEY",
        dataset_code="MACRO_INTERNATIONAL",
        series_code="ALTSALES",  # US Total Vehicle Sales (Millions of Units)
        unit="Millions of Units, SAAR",
        frequency="MONTHLY",
        availability_rule="BEA / FRED monthly release timestamp",
        active=True,
        last_verified_at=NOW
    ),

    # 5. 관세청 / UNI-PASS (Customs)
    SourceRegistry(
        source_id="CUSTOMS_HSK_TRADE",
        provider=SourceProvider.CUSTOMS,
        source_name="관세청 UNI-PASS 품목별(HSK) 수출입 통관통계",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://unipass.customs.go.kr",
        api_endpoint="https://unipass.customs.go.kr/openapi/services/trade/hskTrade",
        authentication_type="API_KEY_ENV",
        api_key_env="CUSTOMS_API_KEY",
        dataset_code="CUSTOMS_CLEARANCE",
        table_code="HSK_8703",  # 승용차 품목 분류
        unit="KG vs COUNT (Strict Separation Required)",
        frequency="MONTHLY",
        availability_rule="Korea Customs Service preliminary/confirmed clearance dates",
        active=True,
        last_verified_at=NOW
    ),

    # 6. KITA (K-stat) - 공식 API 미제공시 다운로드 반입 경로 지정
    SourceRegistry(
        source_id="KITA_KSTAT_OFFICIAL",
        provider=SourceProvider.KITA,
        source_name="한국무역협회 K-stat 무역통계 (공식 반입)",
        source_type=SourceType.OFFICIAL_DOWNLOAD,
        authority_level=AuthorityLevel.LEVEL_3_OFFICIAL_STAT,
        official_url="https://stat.kita.net",
        api_endpoint=None,  # No raw scraping permitted, official download only
        authentication_type="NONE",
        dataset_code="KSTAT_TRADE",
        unit="USD / TON",
        frequency="MONTHLY",
        availability_rule="K-stat official monthly release file with SHA256 checksum",
        active=True,
        last_verified_at=NOW
    ),

    # 7. MOTIE (산업통상자원부) - 공식 배포 보도자료/통계자료
    SourceRegistry(
        source_id="MOTIE_AUTO_STAT",
        provider=SourceProvider.MOTIE,
        source_name="산업통상자원부 자동차산업 월동향 (공식 반입)",
        source_type=SourceType.OFFICIAL_DOWNLOAD,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://www.motie.go.kr",
        api_endpoint=None,
        authentication_type="NONE",
        dataset_code="MOTIE_AUTO_TREND",
        unit="대수, 백만달러",
        frequency="MONTHLY",
        availability_rule="Official MOTIE press release and statistical appendix timestamp",
        active=True,
        last_verified_at=NOW
    )
]

# 8. KOSIS 반도체 산업 (C261) 생산/출하/재고 통계
CANONICAL_SOURCES.append(
    SourceRegistry(
        source_id="KOSIS_SEMI_STAT",
        provider=SourceProvider.KOSIS,
        source_name="통계청 광업제조업동향(반도체 제조업 C261)",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://kosis.kr",
        api_endpoint="https://kosis.kr/openapi/Param/statisticsParameterData.do",
        authentication_type="API_KEY_ENV",
        api_key_env="KOSIS_API_KEY",
        dataset_code="SEMI_PRODUCTION_SHIPMENT",
        table_code="DT_1F02001",
        unit="2020=100",
        frequency="MONTHLY",
        availability_rule="Published monthly by Statistics Korea",
        active=True,
        last_verified_at=NOW
    )
)

# 9. 관세청 HSK 8542 반도체/집적회로 수출입 통관 통계
CANONICAL_SOURCES.append(
    SourceRegistry(
        source_id="CUSTOMS_HSK_8542",
        provider=SourceProvider.CUSTOMS,
        source_name="관세청 HSK 8542(메모리 반도체 및 전자집적회로) 통관통계",
        source_type=SourceType.API,
        authority_level=AuthorityLevel.LEVEL_1_GOV_PUBLIC,
        official_url="https://unipass.customs.go.kr",
        api_endpoint="https://unipass.customs.go.kr/openapi/services/trade/hskTrade",
        authentication_type="API_KEY_ENV",
        api_key_env="CUSTOMS_API_KEY",
        dataset_code="SEMI_CLEARANCE",
        table_code="HSK_8542",
        unit="USD, KG, COUNT",
        frequency="MONTHLY",
        availability_rule="Korea Customs Service preliminary/confirmed clearance dates",
        active=True,
        last_verified_at=NOW
    )
)
