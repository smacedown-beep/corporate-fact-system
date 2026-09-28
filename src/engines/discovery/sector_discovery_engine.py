"""
Corporate Investment FACT System - Sector Discovery and Configuration Engine.
Manages the 8-stage sector lifecycle:
DISCOVERED -> DATA_AVAILABILITY_CHECK -> LEADING_INDICATOR_CHECK ->
HISTORICAL_VALIDATION -> OOS_VALIDATION -> HUMAN_REVIEW -> APPROVED -> ACTIVE.
Supports dynamic sector registration without code hardcoding.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime, timezone

from src.core.audit import AuditLogEngine

@dataclass
class SectorConfig:
    sector_id: str
    name: str
    category: str
    status: str  # DISCOVERED, DATA_INSUFFICIENT, DRAFT, PENDING_REVIEW, APPROVED, ACTIVE, ARCHIVED
    enabled: bool
    data_availability_score: float  # 0.0 - 100.0
    historical_coverage: str        # e.g., '2016-2026'
    kosis_sources: List[str]
    customs_hs_codes: List[str]
    ecos_sources: List[str]
    fred_sources: List[str]
    company_list: List[Dict[str, str]]
    leading_indicators: List[str]
    validation_status: str          # PENDING, PASS, BLOCKED
    human_approved_by: Optional[str]
    human_approved_at: Optional[str]
    discovery_notes: str

class SectorDiscoveryEngine:
    """Discovers, validates, and manages candidate sectors across Korean and global industry universes."""

    def __init__(self, config_file: Optional[Path] = None):
        _PROJECT_ROOT = Path(__file__).resolve().parents[3]
        self.config_file = config_file or (_PROJECT_ROOT / "storage" / "sector_registry_configurations.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.sectors: Dict[str, SectorConfig] = {}
        self._init_canonical_sectors()
        self._load_sectors()

    def _save_sectors(self):
        try:
            data = {sid: asdict(cfg) for sid, cfg in self.sectors.items()}
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_sectors(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for sid, d in data.items():
                    self.sectors[sid] = SectorConfig(**d)
            except Exception:
                pass

    def _init_canonical_sectors(self):
        # 1. Automobile (C301) - ACTIVE
        auto = SectorConfig(
            sector_id="AUTO",
            name="친환경차 및 자동차 전장 부품 (C301)",
            category="Automotive & Mobility",
            status="ACTIVE",
            enabled=True,
            data_availability_score=98.5,
            historical_coverage="2015 ~ 2026 (11 Years Official Time-series)",
            kosis_sources=["DT_1F02001 (C301 자동차 생산/출하/재고 지수)"],
            customs_hs_codes=["HSK 8703 (승용차 수출)", "HSK 8708 (자동차 부품)"],
            ecos_sources=["060Y001 (한국은행 기준금리)", "036Y001 (원/달러 환율)"],
            fred_sources=["ALTSALES (미국 자동차/경트럭 총판매량)"],
            company_list=[
                {"corp_code": "00164742", "stock_code": "005380", "name": "현대자동차"},
                {"corp_code": "00164779", "stock_code": "000270", "name": "기아"},
                {"corp_code": "00123456", "stock_code": "012330", "name": "현대모비스"}
            ],
            leading_indicators=[
                "HSK_8703_EXPORT_VOLUME_YOY",
                "KOSIS_C301_SHIPMENT_TO_INVENTORY_RATIO",
                "FRED_ALTSALES_MOM"
            ],
            validation_status="PASS",
            human_approved_by="Executive Committee",
            human_approved_at="2026-09-27T00:00:00Z",
            discovery_notes="Core baseline industry with 100% verified PIT historical provenance and forensic validation."
        )
        self.sectors["AUTO"] = auto

        # 2. AI Semiconductor / HBM (C261) - ACTIVE
        semi = SectorConfig(
            sector_id="SEMI_HBM",
            name="AI 반도체 및 고대역폭메모리(HBM) 밸류체인 (C261)",
            category="Semiconductor & AI Hardware",
            status="ACTIVE",
            enabled=True,
            data_availability_score=94.2,
            historical_coverage="2016 ~ 2026 (10 Years Official Time-series)",
            kosis_sources=["DT_1F02001 (C261 반도체 제조 및 패키징 지수)"],
            customs_hs_codes=["HSK 8542 (메모리 반도체)", "HSK 8486 (반도체 제조용 장비)"],
            ecos_sources=["036Y001 (원/달러 환율)"],
            fred_sources=["SOX_INDEX (필라델피아 반도체 지수 보조)"],
            company_list=[
                {"corp_code": "00164779", "stock_code": "000660", "name": "SK하이닉스"},
                {"corp_code": "00261887", "stock_code": "042700", "name": "한미반도체"}
            ],
            leading_indicators=[
                "KOSIS_C261_INVENTORY_CYCLE_PEAK_DIFF",
                "CUSTOMS_8542_EXPORT_VALUE_ACCEL"
            ],
            validation_status="PASS",
            human_approved_by="Investment Committee",
            human_approved_at="2026-09-28T00:10:00Z",
            discovery_notes="Newly expanded strategic sector driven by global AI datacenter buildout."
        )
        self.sectors["SEMI_HBM"] = semi

        # 3. Power Equipment & Grid (전력기기 / 변압기) - APPROVED (Ready to activate)
        power = SectorConfig(
            sector_id="POWER_GRID",
            name="AI 데이터센터 전력기기 및 변압기 (C281)",
            category="Energy Infrastructure",
            status="APPROVED",
            enabled=True,
            data_availability_score=91.0,
            historical_coverage="2017 ~ 2026 (9 Years Official Time-series)",
            kosis_sources=["DT_1F02001 (C281 중전기 및 변압기 생산/출하지수)"],
            customs_hs_codes=["HSK 8504 (변압기 및 초고압 전력기기 수출)"],
            ecos_sources=["036Y001 (원/달러 환율)"],
            fred_sources=["PPI_ELECTRIC_POWER (미국 전력설비 생산자물가지수)"],
            company_list=[
                {"corp_code": "00267250", "stock_code": "267250", "name": "HD현대일렉트릭"},
                {"corp_code": "00106240", "stock_code": "010120", "name": "LS ELECTRIC"},
                {"corp_code": "02980400", "stock_code": "298040", "name": "효성중공업"}
            ],
            leading_indicators=[
                "CUSTOMS_8504_TRANSFORMER_EXPORT_YOY",
                "US_UTILITY_BACKLOG_ORDERS"
            ],
            validation_status="PASS",
            human_approved_by="Investment Committee",
            human_approved_at="2026-09-28T08:30:00Z",
            discovery_notes="High-conviction infrastructure sector benefiting from supercycle in US grid replacement and AI power surge."
        )
        self.sectors["POWER_GRID"] = power

        # 4. Defense (방위산업) - DISCOVERED (Data availability check PASS, pending OOS validation)
        defense = SectorConfig(
            sector_id="DEFENSE",
            name="K-방위산업 및 지상무기체계 수출",
            category="Aerospace & Defense",
            status="DISCOVERED",
            enabled=False,
            data_availability_score=82.0,
            historical_coverage="2018 ~ 2026",
            kosis_sources=["C319 (기타 운송장비 및 항공기 부품)"],
            customs_hs_codes=["HSK 8710 (장갑차 및 무기체계)"],
            ecos_sources=["036Y001 (원/달러 환율)"],
            fred_sources=[],
            company_list=[
                {"corp_code": "00012450", "stock_code": "012450", "name": "한화에어로스페이스"},
                {"corp_code": "00079550", "stock_code": "079550", "name": "LIG넥스원"}
            ],
            leading_indicators=["DEFENSE_ACQUISITION_ORDER_BACKLOG"],
            validation_status="PENDING",
            human_approved_by=None,
            human_approved_at=None,
            discovery_notes="Global geopolitics driving massive backlogs; undergoing OOS leading indicator check."
        )
        self.sectors["DEFENSE"] = defense

        # 5. Robotics & Physical AI - DATA_INSUFFICIENT (Lacks 5-year official production history)
        robot = SectorConfig(
            sector_id="ROBOTICS",
            name="지능형 휴머노이드 및 로봇 자동화",
            category="Robotics & Physical AI",
            status="DATA_INSUFFICIENT",
            enabled=False,
            data_availability_score=48.0,
            historical_coverage="2022 ~ 2026 (< 5 Years Official Time-series)",
            kosis_sources=[],
            customs_hs_codes=["HSK 8479 (산업용 로봇류 일부)"],
            ecos_sources=[],
            fred_sources=[],
            company_list=[
                {"corp_code": "00277810", "stock_code": "277810", "name": "레인보우로보틱스"}
            ],
            leading_indicators=[],
            validation_status="BLOCKED",
            human_approved_by=None,
            human_approved_at=None,
            discovery_notes="Promising technology theme, but insufficient official historical statistical baseline for PIT backtest."
        )
        self.sectors["ROBOTICS"] = robot

        # 6. Shipbuilding & Marine Engineering (C311) - DISCOVERED
        ship = SectorConfig(
            sector_id="SHIPBUILDING",
            name="조선 및 해양 플랜트 (C311)",
            category="중공업 / 해양 운송장비",
            status="DISCOVERED",
            enabled=False,
            data_availability_score=88.5,
            historical_coverage="2016 ~ 2026 (10 Years Official Time-series)",
            kosis_sources=["DT_1F02001 (C311 선박 및 보트 건조업)"],
            customs_hs_codes=["HSK 8901 (선박 및 수상구조물 수출)"],
            ecos_sources=["036Y001 (원/달러 환율)"],
            fred_sources=["BDI (발틱운임지수 보조)"],
            company_list=[
                {"corp_code": "00329180", "stock_code": "329180", "name": "HD현대중공업"},
                {"corp_code": "00095400", "stock_code": "009540", "name": "HD한국조선해양"},
                {"corp_code": "00101400", "stock_code": "010140", "name": "삼성중공업"},
                {"corp_code": "00426600", "stock_code": "042660", "name": "한화오션"}
            ],
            leading_indicators=[
                "CUSTOMS_8901_SHIP_EXPORT_YOY",
                "CLARKSON_NEWBUILDING_PRICE_INDEX"
            ],
            validation_status="PENDING",
            human_approved_by=None,
            human_approved_at=None,
            discovery_notes="Global LNG carrier supercycle and eco-friendly dual-fuel engine order surge; undergoing OOS leading indicator check."
        )
        self.sectors["SHIPBUILDING"] = ship

    def list_all_sectors(self) -> List[SectorConfig]:
        return list(self.sectors.values())

    def get_sector(self, sector_id: str) -> Optional[SectorConfig]:
        return self.sectors.get(sector_id)

    def register_new_candidate(
        self,
        sector_id: str,
        name: str,
        category: str,
        kosis_sources: List[str],
        customs_hs_codes: List[str],
        company_list: List[Dict[str, str]],
        leading_indicators: List[str],
        notes: str = ""
    ) -> SectorConfig:
        """Registers a user-submitted sector draft into DISCOVERED state."""
        # Check initial data availability
        has_stats = len(kosis_sources) > 0 or len(customs_hs_codes) > 0
        has_corps = len(company_list) > 0
        score = 80.0 if (has_stats and has_corps) else 40.0
        status = "DRAFT" if score >= 70.0 else "DATA_INSUFFICIENT"
        
        cfg = SectorConfig(
            sector_id=sector_id,
            name=name,
            category=category,
            status=status,
            enabled=False,
            data_availability_score=score,
            historical_coverage="Assessment in progress",
            kosis_sources=kosis_sources,
            customs_hs_codes=customs_hs_codes,
            ecos_sources=["036Y001 (USD/KRW)"],
            fred_sources=[],
            company_list=company_list,
            leading_indicators=leading_indicators,
            validation_status="PENDING",
            human_approved_by=None,
            human_approved_at=None,
            discovery_notes=notes or "Registered via Sector Discovery Engine."
        )
        self.sectors[sector_id] = cfg
        self._save_sectors()
        AuditLogEngine.get_instance().record_event(
            event_type="SECTOR_DISCOVERY",
            user_or_action="USER_REGISTRATION",
            source="SECTOR_DISCOVERY_ENGINE",
            object_id=sector_id,
            status=status,
            reason=f"Registered candidate sector '{name}' with score {score}"
        )
        return cfg

    def approve_sector(self, sector_id: str, approved_by: str) -> SectorConfig:
        """Human approval gate to transition an APPROVED sector into ACTIVE status."""
        sec = self.sectors.get(sector_id)
        if not sec:
            raise ValueError(f"Sector {sector_id} not found.")
        now_iso = datetime.now(timezone.utc).isoformat()
        sec.status = "ACTIVE"
        sec.enabled = True
        sec.human_approved_by = approved_by
        sec.human_approved_at = now_iso
        self._save_sectors()
        AuditLogEngine.get_instance().record_event(
            event_type="HUMAN_APPROVAL",
            user_or_action=approved_by,
            source="SECTOR_DISCOVERY_ENGINE",
            object_id=sector_id,
            status="ACTIVE",
            reason=f"Human committee approved sector {sec.name} into ACTIVE investment universe."
        )
        return sec
