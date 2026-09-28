"""
Corporate Idle Cash Investment Decision Engine (1~2 Year Horizon).
Supports Hanam Electric and Newmotech.
Supports Bond-Free Strategy (Cash/MMF + Multi-Sector FACT Equities)
and dynamic sector expansion (Automotive, Semiconductor, Battery, etc.).
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.core.exceptions import LookaheadBiasError
from src.engines.pit.validator import PitValidator


@dataclass
class SectorAllocation:
    sector_name: str
    target_company: str
    corp_code: str
    stock_code: str
    allocation_pct: Decimal
    verified_eps: Decimal
    fair_pe: Decimal
    target_price: Decimal
    status: str = "FACT_VERIFIED"


@dataclass
class AllocationProposal:
    company_name: str
    decision_date: datetime
    horizon_months: int  # 12~24 months
    idle_cash_amount: Decimal
    include_bonds: bool
    recommended_cash_equiv_pct: Decimal
    recommended_bond_pct: Decimal
    recommended_equity_total_pct: Decimal
    sector_allocations: List[SectorAllocation] = field(default_factory=list)
    benchmark_hurdle_rate: Decimal = Decimal("3.65")
    status: str = "HUMAN_APPROVAL_REQUIRED"


class CorporateCashAllocator:
    def __init__(self, include_bonds: bool = False):
        # Default: Exclude bonds per corporate client policy
        self.include_bonds = include_bonds

    def evaluate_multi_sector_allocation(
        self,
        corporate_client: str,  # "하남전기㈜" or "뉴모텍㈜"
        idle_cash_amount: Decimal,
        decision_date: datetime,
        verified_sectors: List[SectorAllocation],
        benchmark_rate: Decimal = Decimal("3.65"),
        include_bonds: Optional[bool] = None,
        cash_buffer_pct: Decimal = Decimal("20.0")
    ) -> AllocationProposal:
        """
        Allocates idle cash across Cash buffer and verified Sector Equities.
        Completely excludes bonds when include_bonds is False.
        """
        use_bonds = self.include_bonds if include_bonds is None else include_bonds

        if not verified_sectors:
            raise ValueError("At least one verified sector is required for allocation.")

        if use_bonds:
            cash_pct = Decimal("30.0")
            bond_pct = Decimal("40.0")
            equity_total_pct = Decimal("30.0")
        else:
            # 채권 전면 배제 전략:
            # 운영 안정성을 위한 최소 MMF/현금 버퍼 (예: 20%)
            # 나머지 80%를 검증된 유망 섹터 FACT 주식에 분산 배분
            cash_pct = cash_buffer_pct
            bond_pct = Decimal("0.0")
            equity_total_pct = Decimal("100.0") - cash_pct

        # Equal or weighted distribution among verified sectors
        sector_count = Decimal(str(len(verified_sectors)))
        per_sector_pct = (equity_total_pct / sector_count).quantize(Decimal("0.1"))

        allocated_sectors = []
        for sec in verified_sectors:
            allocated_sectors.append(
                SectorAllocation(
                    sector_name=sec.sector_name,
                    target_company=sec.target_company,
                    corp_code=sec.corp_code,
                    stock_code=sec.stock_code,
                    allocation_pct=per_sector_pct,
                    verified_eps=sec.verified_eps,
                    fair_pe=sec.fair_pe,
                    target_price=sec.target_price,
                    status="FACT_VERIFIED"
                )
            )

        return AllocationProposal(
            company_name=corporate_client,
            decision_date=decision_date,
            horizon_months=18,
            idle_cash_amount=idle_cash_amount,
            include_bonds=use_bonds,
            recommended_cash_equiv_pct=cash_pct,
            recommended_bond_pct=bond_pct,
            recommended_equity_total_pct=equity_total_pct,
            sector_allocations=allocated_sectors,
            benchmark_hurdle_rate=benchmark_rate,
            status="HUMAN_APPROVAL_REQUIRED"
        )
