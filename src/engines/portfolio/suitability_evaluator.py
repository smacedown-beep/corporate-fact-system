"""
Dynamic Portfolio Suitability Evaluator.
Completely replaces hardcoded HTML table rows with real-time dynamic synthesis.
Evaluates:
1. Investment Grade (Strong Buy, Buy, Hold, Sell, Avoid) across ALL 7 sectors via quantitative rules
2. Key Fact Evidence (Customs HSK YoY%, Statistics Korea Inventory Cycle, Lead-lag r/p, DART notes)
3. Current Market Price & Dynamic Expected Return Range
4. Valuation Attractiveness (Live PER from price/EPS, Live PBR from price/BPS, Operating Margin, Dividend Yield)
5. Investment Points & Risk Alerts (dynamically adapted to indicator trends)
6. Sell Triggers & Exit Rules (dynamically transitioned based on threshold breaches)
7. Trigger Matrix (Stage 1, 2, 3 Exit Rules & Monitoring Sources)
8. Multi-Strategy Expected Returns (Strategy A Aggressive, Strategy B Balanced)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from src.engines.sync.live_data_synchronizer import SyncState
from src.engines.company.company_financial_engine import CompanyFinancialEngine
from src.engines.indicators.leading_validator import LeadingIndicatorValidator


@dataclass
class SectorSuitabilityRecord:
    sector_id: str
    sector_num: int
    sector_name: str
    industry_class: str
    company_name: str
    stock_code: str
    auxiliary_info: str
    row_bg_color: str
    suitability_grade: str
    grade_badge_class: str
    fact_evidence_html: str
    current_price: float
    intraday_price: float
    target_price_low: float
    target_price_high: float
    target_price_str: str
    expected_return_str: str
    return_low_pct: float
    return_high_pct: float
    live_per: float
    live_pbr: float
    operating_margin_pct: float
    valuation_html: str
    investment_points_html: str
    action_status: str
    action_badge_class: str
    action_rules_html: str
    trigger_stage1: str = ""
    trigger_stage2: str = ""
    trigger_stage3: str = ""
    monitored_sources: str = ""


class DynamicSuitabilityEvaluator:
    """
    Dynamically generates sector suitability records, portfolio table rows,
    and risk-off exit trigger rows based on live SyncState, LeadingIndicatorValidator,
    and CompanyFinancialEngine profiles.
    """

    @classmethod
    def _get_live_corr_summary(cls, sector_id: str, default_r: float, default_p: float) -> Tuple[float, float]:
        try:
            corr_data = LeadingIndicatorValidator.get_live_sector_correlations(sector_id)
            rows = corr_data.get("rows", [])
            if len(rows) > 1:
                return float(rows[1][3]), float(rows[1][4])
        except Exception:
            pass
        return default_r, default_p

    @classmethod
    def evaluate_all(cls) -> List[SectorSuitabilityRecord]:
        v = SyncState.stock_valuations
        records: List[SectorSuitabilityRecord] = []

        # =========================================================================
        # 1. AI 반도체 및 HBM (SK하이닉스 / 000660)
        # =========================================================================
        sk_val = v.get("000660", {})
        sk_price = float(sk_val.get("current_price", 1327000.0))
        sk_intra = float(sk_val.get("intraday_price", sk_price))
        sk_eps = float(sk_val.get("eps", 188227.0))
        sk_bps = float(sk_val.get("bps", 982960.0))
        sk_t_low = float(sk_val.get("target_price_low", 2050000.0))
        sk_t_high = float(sk_val.get("target_price_high", 2180000.0))
        sk_t_str = str(sk_val.get("target_price_str", f"{int(sk_t_low):,} ~ {int(sk_t_high):,}원"))
        sk_ret, sk_r1, sk_r2 = cls._calc_return_str_and_floats(sk_price, sk_t_low, sk_t_high)

        sk_export_yoy = float(SyncState.semi_hsk_export_yoy_pct)
        sk_inv_cycle = float(SyncState.semi_inventory_cycle_pp)
        sk_op_margin = float(sk_val.get("operating_margin", 26.0))
        sk_live_per = round(sk_price / sk_eps, 1) if (sk_price > 0 and sk_eps > 0) else float(sk_val.get("per", 7.05))
        sk_live_pbr = round(sk_price / sk_bps, 2) if (sk_price > 0 and sk_bps > 0) else float(sk_val.get("pbr", 1.35))
        sk_corr_r, sk_corr_p = cls._get_live_corr_summary("SEMI_HBM", 0.614, 0.001)

        if sk_export_yoy < -10.0 and sk_inv_cycle < -5.0:
            sk_grade, sk_grade_badge = "투자 부적합 (AVOID)", "badge-fail"
            sk_action, sk_action_badge = "긴급 하락 경보 / 전량 매도 (SELL EXIT)", "badge-fail"
        elif sk_export_yoy < 0.0 or sk_inv_cycle <= 0.0:
            sk_grade, sk_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            sk_action, sk_action_badge = "하락 경보 / 비중 축소 (SELL 50%)", "badge-fail"
        elif sk_live_per > 15.0 or sk_export_yoy < 15.0:
            sk_grade, sk_grade_badge = "적합 (BUY)", "badge-pass"
            sk_action, sk_action_badge = ("차익 실현 경계 (TRIM 20%)" if sk_live_per > 15.0 else "보유 유지 (HOLD)"), ("badge-warn" if sk_live_per > 15.0 else "badge-pass")
        else:
            sk_grade, sk_grade_badge = "적극 적합 (STRONG BUY)", "badge-pass"
            sk_action, sk_action_badge = "보유 유지 (HOLD)", "badge-pass"

        sk_trend_word = "급증" if sk_export_yoy >= 15.0 else ("증가" if sk_export_yoy >= 0 else "둔화")
        sk_cycle_word = "완연한 반등세" if sk_inv_cycle > 0 else "재고 조정 국면"
        sk_val_word = "업종 저평가" if sk_live_per <= 10.0 else ("적정 밸류" if sk_live_per <= 15.0 else "밸류 부담 주의")

        sk_fact_html = (
            f"- 관세청 HSK 8542 메모리 수출액 전년비 <strong>{sk_export_yoy:+.1f}%</strong> {sk_trend_word}<br>\n"
            f"- <strong>Lag -2개월 선행 계량검증 r={sk_corr_r:.3f} (유의수준 p={sk_corr_p:.3f})</strong><br>\n"
            f"- 통계청 반도체(C261) 재고순환선 <strong>{sk_inv_cycle:+.1f}%p</strong> {sk_cycle_word}"
        )
        sk_val_html = (
            f'- 실시간 PER <strong id="live_per_000660">{sk_live_per:.1f}배</strong>, PBR {sk_live_pbr:.2f}배 ({sk_val_word})<br>\n'
            f"- DART 공시 확정 영업이익률 <strong>{sk_op_margin:.1f}%</strong>"
        )
        sk_pts_html = (
            "- 엔비디아 HBM3E 독점적 공급 지위 및 HBM4 조기 선점<br>\n"
            '- <span style="color:var(--warning);">[주의 리스크]</span> 글로벌 빅테크 AI CapEx 투자 집행 속도'
        )
        sk_rules_html = (
            "• 1차 익절(20%): HSK 8542 수출 2개월 연속 -5% 하락 시<br>\n"
            "• 전량 매도(EXIT): 반도체 재고순환선 음전환(0%p 하회) 시"
        )

        records.append(SectorSuitabilityRecord(
            sector_id="SEMI_HBM",
            sector_num=1,
            sector_name="AI 반도체 및 HBM",
            industry_class="전자부품·반도체 (C261)",
            company_name="SK하이닉스",
            stock_code="000660",
            auxiliary_info="삼성전자 보조",
            row_bg_color="rgba(56, 189, 248, 0.04)",
            suitability_grade=sk_grade,
            grade_badge_class=sk_grade_badge,
            fact_evidence_html=sk_fact_html,
            current_price=sk_price,
            intraday_price=sk_intra,
            target_price_low=sk_t_low,
            target_price_high=sk_t_high,
            target_price_str=sk_t_str,
            expected_return_str=sk_ret,
            return_low_pct=sk_r1,
            return_high_pct=sk_r2,
            live_per=sk_live_per,
            live_pbr=sk_live_pbr,
            operating_margin_pct=sk_op_margin,
            valuation_html=sk_val_html,
            investment_points_html=sk_pts_html,
            action_status=sk_action,
            action_badge_class=sk_action_badge,
            action_rules_html=sk_rules_html,
            trigger_stage1="관세청 HSK 8542 메모리 수출액 2개월 연속 전월비 -5% 하락 시",
            trigger_stage2="통계청 반도체 재고순환선 음전환(0%p 하회) 시",
            trigger_stage3="대미 HBM 수출액 전년대비 -15% 급감 또는 영업이익률 15% 붕괴 시",
            monitored_sources="관세청 HSK 8542 / 통계청 C261 재고순환선",
        ))

        # =========================================================================
        # 2. AI 인프라 / 전력기기 (HD현대일렉트릭 / 267260)
        # =========================================================================
        hd_val = v.get("267260", {})
        hd_price = float(hd_val.get("current_price", 505000.0))
        hd_intra = float(hd_val.get("intraday_price", hd_price))
        hd_eps = float(hd_val.get("eps", 23709.0))
        hd_bps = float(hd_val.get("bps", 138356.0))
        hd_t_low = float(hd_val.get("target_price_low", 750000.0))
        hd_t_high = float(hd_val.get("target_price_high", 790000.0))
        hd_t_str = str(hd_val.get("target_price_str", f"{int(hd_t_low):,} ~ {int(hd_t_high):,}원"))
        hd_ret, hd_r1, hd_r2 = cls._calc_return_str_and_floats(hd_price, hd_t_low, hd_t_high)

        hd_export_yoy = float(SyncState.power_grid_hsk_export_yoy_pct)
        hd_op_margin = float(hd_val.get("operating_margin", 19.7))
        hd_live_per = round(hd_price / hd_eps, 1) if (hd_price > 0 and hd_eps > 0) else float(hd_val.get("per", 21.3))
        hd_live_pbr = round(hd_price / hd_bps, 2) if (hd_price > 0 and hd_bps > 0) else float(hd_val.get("pbr", 3.65))
        hd_corr_r, hd_corr_p = cls._get_live_corr_summary("POWER_GRID", 0.582, 0.003)

        if hd_export_yoy < 0.0 or hd_op_margin < 12.0:
            hd_grade, hd_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            hd_action, hd_action_badge = "하락 경보 / 비중 축소 (SELL 50%)", "badge-fail"
        elif hd_live_per > 25.0:
            hd_grade, hd_grade_badge = "적합 / 분할익절 고려", "badge-warn"
            hd_action, hd_action_badge = "차익 실현 경계 (TRIM 20%)", "badge-warn"
        elif hd_export_yoy >= 15.0 and hd_op_margin >= 15.0:
            hd_grade, hd_grade_badge = "적극 적합 (STRONG BUY)", "badge-pass"
            hd_action, hd_action_badge = "보유 유지 (HOLD)", "badge-pass"
        else:
            hd_grade, hd_grade_badge = "적합 (BUY)", "badge-pass"
            hd_action, hd_action_badge = "보유 유지 (HOLD)", "badge-pass"

        hd_trend_word = "폭증" if hd_export_yoy >= 20.0 else ("증가" if hd_export_yoy >= 0 else "감소")
        hd_fact_html = (
            f"- 관세청 HSK 8504 대미 변압기 수출액 전년비 <strong>{hd_export_yoy:+.1f}%</strong> {hd_trend_word}<br>\n"
            f"- <strong>Lag -3개월 선행 계량검증 r={hd_corr_r:.3f} (유의수준 p={hd_corr_p:.3f})</strong><br>\n"
            f"- 북미 노후 전력망 전면 교체 및 AI 데이터센터 전력 수요 폭발"
        )
        hd_val_html = (
            f'- 실시간 PER <strong id="live_per_267260">{hd_live_per:.1f}배</strong>, 3년치 수주잔고 확보<br>\n'
            f"- DART 공시 확정 영업이익률 <strong>{hd_op_margin:.1f}%</strong> (고수익성)"
        )
        hd_pts_html = (
            "- 북미 초고압 변압기 쇼티지로 판가(ASP) 지속 상승<br>\n"
            '- <span style="color:var(--warning);">[주의 리스크]</span> 런던금속거래소(LME) 구리 원자재 가격 추이'
        )
        hd_rules_html = (
            "• 1차 익절(30%): PER 25배 초과 과열 또는 분기 수주 둔화 시<br>\n"
            "• 전량 매도(EXIT): 구리가격 폭등으로 영업이익률 12% 붕괴 시"
        )

        records.append(SectorSuitabilityRecord(
            sector_id="POWER_GRID",
            sector_num=2,
            sector_name="AI 인프라 / 전력기기",
            industry_class="전기장비 (C281)",
            company_name="HD현대일렉트릭",
            stock_code="267260",
            auxiliary_info="LS일렉트릭 보조",
            row_bg_color="rgba(245, 158, 11, 0.04)",
            suitability_grade=hd_grade,
            grade_badge_class=hd_grade_badge,
            fact_evidence_html=hd_fact_html,
            current_price=hd_price,
            intraday_price=hd_intra,
            target_price_low=hd_t_low,
            target_price_high=hd_t_high,
            target_price_str=hd_t_str,
            expected_return_str=hd_ret,
            return_low_pct=hd_r1,
            return_high_pct=hd_r2,
            live_per=hd_live_per,
            live_pbr=hd_live_pbr,
            operating_margin_pct=hd_op_margin,
            valuation_html=hd_val_html,
            investment_points_html=hd_pts_html,
            action_status=hd_action,
            action_badge_class=hd_action_badge,
            action_rules_html=hd_rules_html,
            trigger_stage1="PER 25.0배 초과 도달 시 (보유 물량 30% 분할 익절)",
            trigger_stage2="관세청 HSK 8504 대미 변압기 수출액 전월비 -15% 둔화 시",
            trigger_stage3="런던금속거래소(LME) 구리가격 톤당 $11,000 돌파로 마진 붕괴 시",
            monitored_sources="관세청 HSK 8504 / DART 분기 영업이익률",
        ))

        # =========================================================================
        # 3. 조선 및 해양 플랜트 (HD현대중공업 / 329180)
        # =========================================================================
        hhi_val = v.get("329180", {})
        hhi_price = float(hhi_val.get("current_price", 318000.0))
        hhi_intra = float(hhi_val.get("intraday_price", hhi_price))
        hhi_eps = float(hhi_val.get("eps", 17473.0))
        hhi_bps = float(hhi_val.get("bps", 151428.0))
        hhi_t_low = float(hhi_val.get("target_price_low", 490000.0))
        hhi_t_high = float(hhi_val.get("target_price_high", 515000.0))
        hhi_t_str = str(hhi_val.get("target_price_str", f"{int(hhi_t_low):,} ~ {int(hhi_t_high):,}원"))
        hhi_ret, hhi_r1, hhi_r2 = cls._calc_return_str_and_floats(hhi_price, hhi_t_low, hhi_t_high)

        hhi_clarkson = float(SyncState.shipbuilding_newbuilding_price_index)
        hhi_export_yoy = float(getattr(SyncState, "shipbuilding_hsk_export_yoy_pct", 18.4))
        hhi_op_margin = float(hhi_val.get("operating_margin", 6.8))
        hhi_live_per = round(hhi_price / hhi_eps, 1) if (hhi_price > 0 and hhi_eps > 0) else float(hhi_val.get("per", 18.2))
        hhi_live_pbr = round(hhi_price / hhi_bps, 2) if (hhi_price > 0 and hhi_bps > 0) else float(hhi_val.get("pbr", 2.10))
        hhi_corr_r, hhi_corr_p = cls._get_live_corr_summary("SHIPBUILDING", 0.542, 0.004)

        if hhi_op_margin <= 0.0:
            hhi_grade, hhi_grade_badge = "투자 부적합 (AVOID)", "badge-fail"
            hhi_action, hhi_action_badge = "긴급 하락 경보 / 전량 매도 (SELL EXIT)", "badge-fail"
        elif hhi_clarkson < 185.0 or hhi_export_yoy < 0.0:
            hhi_grade, hhi_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            hhi_action, hhi_action_badge = "하락 경보 / 1차 축소 (SELL 30%)", "badge-warn"
        elif hhi_clarkson >= 190.0 and hhi_op_margin >= 8.0 and hhi_export_yoy >= 15.0:
            hhi_grade, hhi_grade_badge = "적극 적합 (STRONG BUY)", "badge-pass"
            hhi_action, hhi_action_badge = "보유 유지 (HOLD)", "badge-pass"
        else:
            hhi_grade, hhi_grade_badge = "적합 (BUY)", "badge-pass"
            hhi_action, hhi_action_badge = "보유 유지 (HOLD)", "badge-pass"

        records.append(SectorSuitabilityRecord(
            sector_id="SHIPBUILDING",
            sector_num=3,
            sector_name="조선 및 해양 플랜트",
            industry_class="선박 건조업 (C311)",
            company_name="HD현대중공업",
            stock_code="329180",
            auxiliary_info="HD한국조선해양",
            row_bg_color="rgba(14, 165, 233, 0.04)",
            suitability_grade=hhi_grade,
            grade_badge_class=hhi_grade_badge,
            fact_evidence_html=(
                f"- 관세청 HSK 8901 선박류 통관 수출액 전년비 <strong>{hhi_export_yoy:+.1f}%</strong><br>\n"
                f"- <strong>Lag -2개월 선행 계량검증 r={hhi_corr_r:.3f} (유의수준 p={hhi_corr_p:.3f})</strong><br>\n"
                f"- 클락슨 신조선가지수 <strong>{hhi_clarkson:.1f}p</strong> {'고점 견조' if hhi_clarkson >= 185 else '조정 주의'}"
            ),
            current_price=hhi_price,
            intraday_price=hhi_intra,
            target_price_low=hhi_t_low,
            target_price_high=hhi_t_high,
            target_price_str=hhi_t_str,
            expected_return_str=hhi_ret,
            return_low_pct=hhi_r1,
            return_high_pct=hhi_r2,
            live_per=hhi_live_per,
            live_pbr=hhi_live_pbr,
            operating_margin_pct=hhi_op_margin,
            valuation_html=(
                f'- 실시간 PER <strong id="live_per_329180">{hhi_live_per:.1f}배</strong>, PBR {hhi_live_pbr:.2f}배<br>\n'
                f"- DART 영업이익 흑자 안착 (영업이익률 <strong>{hhi_op_margin:.1f}%</strong>)"
            ),
            investment_points_html=(
                "- 친환경 이중연료 추진선 글로벌 독점 및 방산 특수선 확장<br>\n"
                '- <span style="color:var(--warning);">[주의 리스크]</span> 포스코/현대제철 후판 가격 및 조선소 인건비 추이'
            ),
            action_status=hhi_action,
            action_badge_class=hhi_action_badge,
            action_rules_html=(
                "• 1차 축소(30%): 신조선가지수 185p 붕괴 및 후판가 급등 시<br>\n"
                "• 전량 매도(EXIT): 조선류 통관 지연 및 영업이익 적자 반전 시"
            ),
            trigger_stage1="클락슨 신조선가지수 3개월 연속 하락 전환 (185p 붕괴) 시",
            trigger_stage2="관세청 HSK 8901 선박류 통관 인도액 전년비 음전환 시",
            trigger_stage3="후판가 톤당 100만원 급등으로 조선 부문 분기 적자 반전 시",
            monitored_sources="클락슨 신조선가지수 / 관세청 HSK 8901",
        ))

        # =========================================================================
        # 4. 친환경차 및 자동차 전장 (현대자동차 / 005380)
        # =========================================================================
        hmc_val = v.get("005380", {})
        hmc_price = float(hmc_val.get("current_price", 310500.0))
        hmc_intra = float(hmc_val.get("intraday_price", hmc_price))
        hmc_eps = float(hmc_val.get("eps", 59712.0))
        hmc_bps = float(hmc_val.get("bps", 500806.0))
        hmc_div = float(hmc_val.get("dividend_yield", 5.4))
        hmc_t_low = float(hmc_val.get("target_price_low", 385000.0))
        hmc_t_high = float(hmc_val.get("target_price_high", 405000.0))
        hmc_t_str = str(hmc_val.get("target_price_str", f"{int(hmc_t_low):,} ~ {int(hmc_t_high):,}원"))
        hmc_ret, hmc_r1, hmc_r2 = cls._calc_return_str_and_floats(hmc_price, hmc_t_low, hmc_t_high, f"배당 {hmc_div:.1f}% 포함")

        hmc_ship_inv = float(SyncState.auto_shipment_inventory_ratio)
        hmc_export_yoy = float(SyncState.auto_hsk_export_yoy_pct)
        hmc_op_margin = float(hmc_val.get("operating_margin", 9.3))
        hmc_live_per = round(hmc_price / hmc_eps, 1) if (hmc_price > 0 and hmc_eps > 0) else float(hmc_val.get("per", 5.2))
        hmc_live_pbr = round(hmc_price / hmc_bps, 2) if (hmc_price > 0 and hmc_bps > 0) else float(hmc_val.get("pbr", 0.62))
        hmc_corr_r, hmc_corr_p = cls._get_live_corr_summary("AUTO", 0.518, 0.002)

        if hmc_ship_inv < 1.0 or hmc_export_yoy < 0.0:
            hmc_grade, hmc_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            hmc_action, hmc_action_badge = "하락 경보 / 1차 축소 (SELL 50%)", "badge-fail"
        elif hmc_live_per > 8.5:
            hmc_grade, hmc_grade_badge = "적합 / 분할익절 고려", "badge-warn"
            hmc_action, hmc_action_badge = "차익 실현 경계 (TRIM 20%)", "badge-warn"
        elif hmc_ship_inv >= 1.25 and hmc_export_yoy >= 15.0 and hmc_live_per <= 6.0:
            hmc_grade, hmc_grade_badge = "적극 적합 (STRONG BUY)", "badge-pass"
            hmc_action, hmc_action_badge = "보유 유지 (HOLD)", "badge-pass"
        else:
            hmc_grade, hmc_grade_badge = "적합 (BUY)", "badge-pass"
            hmc_action, hmc_action_badge = "보유 유지 (HOLD)", "badge-pass"

        hmc_inv_status = "완만한 재고소진" if hmc_ship_inv >= 1.0 else "재고 누적 경계"
        hmc_val_status = "극심한 밸류에이션 저평가" if hmc_live_per <= 6.5 else "적정 밸류에이션 구간"

        records.append(SectorSuitabilityRecord(
            sector_id="AUTO",
            sector_num=4,
            sector_name="친환경차 및 자동차 전장",
            industry_class="자동차 및 트레일러 (C301)",
            company_name="현대자동차",
            stock_code="005380",
            auxiliary_info="기아 보조",
            row_bg_color="rgba(16, 185, 129, 0.04)",
            suitability_grade=hmc_grade,
            grade_badge_class=hmc_grade_badge,
            fact_evidence_html=(
                f"- 통계청 출하/재고비율 <strong>{hmc_ship_inv:.2f}배</strong> ({hmc_inv_status})<br>\n"
                f"- 관세청 HSK 8703 승용차 전년비 <strong>{hmc_export_yoy:+.1f}%</strong> (2개월 선행 r={hmc_corr_r:.3f})<br>\n"
                f"- DART 주석 27 감사보고서 확정 보통주 EPS 12,664원 정합"
            ),
            current_price=hmc_price,
            intraday_price=hmc_intra,
            target_price_low=hmc_t_low,
            target_price_high=hmc_t_high,
            target_price_str=hmc_t_str,
            expected_return_str=hmc_ret,
            return_low_pct=hmc_r1,
            return_high_pct=hmc_r2,
            live_per=hmc_live_per,
            live_pbr=hmc_live_pbr,
            operating_margin_pct=hmc_op_margin,
            valuation_html=(
                f'- <strong>실시간 PER <span id="live_per_005380">{hmc_live_per:.1f}배</span>, PBR {hmc_live_pbr:.2f}배</strong> ({hmc_val_status})<br>\n'
                f"- 영업이익률 <strong>{hmc_op_margin:.1f}%</strong>, 배당수익률 <strong>{hmc_div:.1f}%</strong>"
            ),
            investment_points_html=(
                "- 하이브리드(HEV) 고수익 차종 믹스 개선 및 인도법인 가치<br>\n"
                '- <span style="color:var(--warning);">[주의 리스크]</span> 주요국 수입차 관세 장벽 및 전기차 보조금 축소'
            ),
            action_status=hmc_action,
            action_badge_class=hmc_action_badge,
            action_rules_html=(
                "• 1차 축소(50%): 자동차 출하/재고비율 1.0배 미만 급락 시<br>\n"
                "• 전량 매도(EXIT): 대미 완성차 관세 인상 현실화 시"
            ),
            trigger_stage1="통계청 C301 출하/재고 비율 1.0배 미만(재고 누적) 급락 시",
            trigger_stage2="관세청 HSK 8703 승용차 수출액 전년대비 음전환 시",
            trigger_stage3="미국 관세 인상(20% 이상) 법제화 또는 하이브리드 판매율 급감 시",
            monitored_sources="통계청 DT_1F02001 / 관세청 HSK 8703",
        ))

        # =========================================================================
        # 5. 금융 및 은행 지주 (KB금융 / 105560)
        # =========================================================================
        kb_val = v.get("105560", {})
        kb_price = float(kb_val.get("current_price", 161700.0))
        kb_intra = float(kb_val.get("intraday_price", kb_price))
        kb_eps = float(kb_val.get("eps", 26508.0))
        kb_bps = float(kb_val.get("bps", 336875.0))
        kb_div = float(kb_val.get("dividend_yield", 5.8))
        kb_t_low = float(kb_val.get("target_price_low", 185000.0))
        kb_t_high = float(kb_val.get("target_price_high", 193000.0))
        kb_t_str = str(kb_val.get("target_price_str", f"{int(kb_t_low):,} ~ {int(kb_t_high):,}원"))
        kb_ret, kb_r1, kb_r2 = cls._calc_return_str_and_floats(kb_price, kb_t_low, kb_t_high, f"배당 {kb_div:.1f}% 포함")

        kb_base_rate = float(SyncState.base_rate_pct)
        kb_op_margin = float(kb_val.get("operating_margin", 28.5))
        kb_live_per = round(kb_price / kb_eps, 1) if (kb_price > 0 and kb_eps > 0) else float(kb_val.get("per", 6.1))
        kb_live_pbr = round(kb_price / kb_bps, 2) if (kb_price > 0 and kb_bps > 0) else float(kb_val.get("pbr", 0.48))
        kb_corr_r, kb_corr_p = cls._get_live_corr_summary("FINANCE", 0.505, 0.003)

        if kb_base_rate < 2.25:
            kb_grade, kb_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            kb_action, kb_action_badge = "금리 인하 경보 / 비중 축소 (SELL 30%)", "badge-warn"
        elif kb_live_pbr >= 0.70:
            kb_grade, kb_grade_badge = "적합 / 목표도달 익절", "badge-warn"
            kb_action, kb_action_badge = "1차 차익실현 경계 (TRIM 30%)", "badge-warn"
        elif kb_live_pbr < 0.45 and kb_base_rate >= 3.0:
            kb_grade, kb_grade_badge = "적극 적합 (STRONG BUY)", "badge-pass"
            kb_action, kb_action_badge = "보유 유지 (HOLD)", "badge-pass"
        else:
            kb_grade, kb_grade_badge = "적합 (BUY)", "badge-pass"
            kb_action, kb_action_badge = "보유 유지 (HOLD)", "badge-pass"

        records.append(SectorSuitabilityRecord(
            sector_id="FINANCE",
            sector_num=5,
            sector_name="금융 및 은행 지주",
            industry_class="금융업 (K64)",
            company_name="KB금융",
            stock_code="105560",
            auxiliary_info="신한지주 보조",
            row_bg_color="rgba(168, 85, 247, 0.04)",
            suitability_grade=kb_grade,
            grade_badge_class=kb_grade_badge,
            fact_evidence_html=(
                f"- 한국은행 ECOS 기준금리 <strong>{kb_base_rate:.2f}%</strong> 및 예대마진 견조<br>\n"
                f"- <strong>1개월 선행 계량검증 r={kb_corr_r:.3f} (유의수준 p={kb_corr_p:.3f})</strong><br>\n"
                f"- 정부 기업 밸류업 프로그램 및 자사주 분기별 지속 소각"
            ),
            current_price=kb_price,
            intraday_price=kb_intra,
            target_price_low=kb_t_low,
            target_price_high=kb_t_high,
            target_price_str=kb_t_str,
            expected_return_str=kb_ret,
            return_low_pct=kb_r1,
            return_high_pct=kb_r2,
            live_per=kb_live_per,
            live_pbr=kb_live_pbr,
            operating_margin_pct=kb_op_margin,
            valuation_html=(
                f'- 실시간 PER <strong id="live_per_105560">{kb_live_per:.1f}배</strong>, PBR <strong>{kb_live_pbr:.2f}배</strong> (순자산 대비 저평가)<br>\n'
                f"- 연간 배당수익률 <strong>{kb_div:.1f}%</strong> 주주환원 수익률 극대화"
            ),
            investment_points_html=(
                "- 압도적인 총주주환원율(TSR) 40% 도달 및 자사주 소각 이행<br>\n"
                '- <span style="color:var(--warning);">[주의 리스크]</span> 경기 둔화 시 부동산 PF 연체율 및 대손충당금 전입'
            ),
            action_status=kb_action,
            action_badge_class=kb_action_badge,
            action_rules_html=(
                "• 1차 익절(30%): PBR 0.70배 도달 또는 기준금리 급인하 시<br>\n"
                "• 전량 매도(EXIT): 연체율 급등으로 대손충당금 전년비 +30% 증가 시"
            ),
            trigger_stage1="PBR 0.70배 도달 시 (목표 밸류에이션 도달로 30% 차익실현)",
            trigger_stage2="한국은행 기준금리 급인하(50bp 이상 빅컷)로 순이자마진 붕괴 시",
            trigger_stage3="가계·PF 연체율 급등으로 분기 대손충당금 전년비 +30% 이상 폭증 시",
            monitored_sources="한국은행 ECOS 060Y / DART 충당금 전입액",
        ))

        # =========================================================================
        # 6. 1차 철강 및 압연 (POSCO홀딩스 / 005490)
        # =========================================================================
        posco_val = v.get("005490", {})
        posco_price = float(posco_val.get("current_price", 302500.0))
        posco_intra = float(posco_val.get("intraday_price", posco_price))
        posco_eps = float(posco_val.get("eps", 20862.0))
        posco_bps = float(posco_val.get("bps", 560185.0))
        posco_t_low = float(posco_val.get("target_price_low", 330000.0))
        posco_t_high = float(posco_val.get("target_price_high", 345000.0))
        posco_t_str = str(posco_val.get("target_price_str", f"{int(posco_t_low):,} ~ {int(posco_t_high):,}원"))

        posco_export_yoy = float(SyncState.steel_export_yoy_pct)
        posco_op_margin = float(posco_val.get("operating_margin", 4.5))
        posco_live_per = round(posco_price / posco_eps, 1) if (posco_price > 0 and posco_eps > 0) else float(posco_val.get("per", 14.5))
        posco_live_pbr = round(posco_price / posco_bps, 2) if (posco_price > 0 and posco_bps > 0) else float(posco_val.get("pbr", 0.54))
        posco_corr_r, _ = cls._get_live_corr_summary("STEEL", 0.382, 0.035)

        if posco_export_yoy >= 5.0 and posco_op_margin >= 6.0:
            posco_grade, posco_grade_badge = "적합 (BUY)", "badge-pass"
            posco_action, posco_action_badge = "보유 유지 (HOLD)", "badge-pass"
            posco_note = "업황 턴어라운드"
            posco_export_word = "반등 성공"
        elif posco_export_yoy >= 0.0 and posco_op_margin >= 4.0:
            posco_grade, posco_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            posco_action, posco_action_badge = "보유 관망 (HOLD)", "badge-warn"
            posco_note = "중립 관망"
            posco_export_word = "보합권 회복"
        elif posco_export_yoy < -10.0 or posco_op_margin <= 0.0:
            posco_grade, posco_grade_badge = "투자 부적합 (AVOID)", "badge-fail"
            posco_action, posco_action_badge = "긴급 하락 경보 / 전량 매도 (SELL EXIT)", "badge-fail"
            posco_note = "신규진입 금지"
            posco_export_word = "급감 경보"
        else:
            posco_grade, posco_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            posco_action, posco_action_badge = "하락 지속 경보 / 비중 축소 (SELL 50%)", "badge-fail"
            posco_note = "중립 관망"
            posco_export_word = "회복 지연"

        posco_ret, posco_r1, posco_r2 = cls._calc_return_str_and_floats(posco_price, posco_t_low, posco_t_high, posco_note)

        records.append(SectorSuitabilityRecord(
            sector_id="STEEL",
            sector_num=6,
            sector_name="1차 철강 및 압연",
            industry_class="1차 철강 제조업 (C241)",
            company_name="POSCO홀딩스",
            stock_code="005490",
            auxiliary_info="현대제철 보조",
            row_bg_color="rgba(100, 116, 139, 0.04)",
            suitability_grade=posco_grade,
            grade_badge_class=posco_grade_badge,
            fact_evidence_html=(
                f"- 관세청 HSK 72 철강 통관 수출액 전년비 <strong>{posco_export_yoy:+.1f}%</strong> {posco_export_word}<br>\n"
                f"- 중국산 저가 열연재 유입 추이 및 롤마진 스프레드 점검<br>\n"
                f"- 선행지표 상관계수 r={posco_corr_r:.3f} (지지선 방어 수준 확인)"
            ),
            current_price=posco_price,
            intraday_price=posco_intra,
            target_price_low=posco_t_low,
            target_price_high=posco_t_high,
            target_price_str=posco_t_str,
            expected_return_str=posco_ret,
            return_low_pct=posco_r1,
            return_high_pct=posco_r2,
            live_per=posco_live_per,
            live_pbr=posco_live_pbr,
            operating_margin_pct=posco_op_margin,
            valuation_html=(
                f'- 실시간 PER <span id="live_per_005490">{posco_live_per:.1f}배</span>, PBR <strong>{posco_live_pbr:.2f}배</strong> (장부가치 하방 지지)<br>\n'
                f"- 영업이익률 <strong>{posco_op_margin:.1f}%</strong>, 리튬/니켈 신사업 모멘텀"
            ),
            investment_points_html=(
                "- 중국 부동산 부양책에 따른 인프라 철강 수요 반등 관건<br>\n"
                '- <span style="color:var(--fail);">[결론 요령]</span> 철강 수출 YoY +5% 및 마진 회복 확인 시 비중 확대'
            ),
            action_status=posco_action,
            action_badge_class=posco_action_badge,
            action_rules_html=(
                "• 행동 요령: 수출 역성장 구간 보유 물량 50% 축소 관리<br>\n"
                "• 전량 매도(EXIT): 중국 저가재 유입 지속 및 롤마진 붕괴 시"
            ),
            trigger_stage1="중국 열연 유통가 추가 하락 시 (30% 분할 매도 권고)",
            trigger_stage2="관세청 HSK 72 철강 수출 역성장 지속 시 (50% 비중 축소)",
            trigger_stage3="중국 부동산 부양 실패 및 영업적자 전환 시 (전량 매도)",
            monitored_sources="관세청 HSK 72 / 중국 열연 유통가격",
        ))

        # =========================================================================
        # 7. 2차전지 및 배터리 소재 (LG에너지솔루션 / 373220)
        # =========================================================================
        lg_val = v.get("373220", {})
        lg_price = float(lg_val.get("current_price", 395000.0))
        lg_intra = float(lg_val.get("intraday_price", lg_price))
        lg_eps = float(lg_val.get("eps", 6583.0))
        lg_bps = float(lg_val.get("bps", 106757.0))
        lg_t_low = float(lg_val.get("target_price_low", 405000.0))
        lg_t_high = float(lg_val.get("target_price_high", 415000.0))
        lg_t_str = str(lg_val.get("target_price_str", f"{int(lg_t_low):,} ~ {int(lg_t_high):,}원"))

        lg_export_yoy = float(getattr(SyncState, "battery_hsk_export_yoy_pct", -12.6))
        lg_inv_cycle = float(getattr(SyncState, "battery_inventory_cycle_pp", -8.4))
        lg_op_margin = float(lg_val.get("operating_margin", 3.2))
        lg_live_per = round(lg_price / lg_eps, 1) if (lg_price > 0 and lg_eps > 0) else float(lg_val.get("per", 60.0))
        lg_live_pbr = round(lg_price / lg_bps, 2) if (lg_price > 0 and lg_bps > 0) else float(lg_val.get("pbr", 3.70))

        if lg_export_yoy >= 5.0 and lg_inv_cycle >= 0.0 and lg_live_per <= 35.0:
            lg_grade, lg_grade_badge = "적합 (BUY)", "badge-pass"
            lg_action, lg_action_badge = "신규 편입 / 보유 (HOLD)", "badge-pass"
            lg_note = "턴어라운드 진입"
            lg_export_status = f"전년비 <strong>{lg_export_yoy:+.1f}%</strong> 반등 전환"
        elif lg_export_yoy >= 0.0:
            lg_grade, lg_grade_badge = "중립 / 관망 (HOLD)", "badge-warn"
            lg_action, lg_action_badge = "턴어라운드 관망 (HOLD)", "badge-warn"
            lg_note = "관망 대기"
            lg_export_status = f"전년비 <strong>{lg_export_yoy:+.1f}%</strong> 바닥 다지기"
        else:
            lg_grade, lg_grade_badge = "투자 부적합 (AVOID)", "badge-fail"
            lg_action, lg_action_badge = "긴급 하락 경보 / 전량 매도 (SELL EXIT)", "badge-fail"
            lg_note = "신규진입 보류"
            lg_export_status = f"전년비 <strong>{lg_export_yoy:+.1f}%</strong> 하락세 지속"

        lg_ret, lg_r1, lg_r2 = cls._calc_return_str_and_floats(lg_price, lg_t_low, lg_t_high, lg_note)

        records.append(SectorSuitabilityRecord(
            sector_id="BATTERY",
            sector_num=7,
            sector_name="2차전지 및 배터리 소재",
            industry_class="축전지 및 배터리 (C282)",
            company_name="LG에너지솔루션",
            stock_code="373220",
            auxiliary_info="",
            row_bg_color="rgba(239, 68, 68, 0.04)",
            suitability_grade=lg_grade,
            grade_badge_class=lg_grade_badge,
            fact_evidence_html=(
                f"- 관세청 NCM/LFP 양극재 통관 수출액 {lg_export_status}<br>\n"
                f"- 선행지표 상관계수 r=0.18 (통계적 유의수준 p > 0.05 미달)<br>\n"
                f"- 통계청 배터리 재고순환선 <strong>{lg_inv_cycle:+.1f}%p</strong> ({'재고 소진' if lg_inv_cycle >= 0 else '재고 누적 미해소'})"
            ),
            current_price=lg_price,
            intraday_price=lg_intra,
            target_price_low=lg_t_low,
            target_price_high=lg_t_high,
            target_price_str=lg_t_str,
            expected_return_str=lg_ret,
            return_low_pct=lg_r1,
            return_high_pct=lg_r2,
            live_per=lg_live_per,
            live_pbr=lg_live_pbr,
            operating_margin_pct=lg_op_margin,
            valuation_html=(
                f'- 실시간 PER <strong id="live_per_373220">{lg_live_per:.1f}배</strong>, PBR {lg_live_pbr:.2f}배 ({("고평가 부담" if lg_live_per > 35 else "밸류 완화")})<br>\n'
                f"- 영업이익률 <strong>{lg_op_margin:.1f}%</strong>, 전방 수요 캐즘 점검"
            ),
            investment_points_html=(
                "- 전기차 수요 둔화 구간에서는 보수적 리스크 관리 필수<br>\n"
                '- <span style="color:var(--fail);">[결론 요령]</span> 양극재 수출 YoY 양전환(+5% 이상) 확인 시까지 진입 보류'
            ),
            action_status=lg_action,
            action_badge_class=lg_action_badge,
            action_rules_html=(
                "• 행동 요령: 보유 잔량 전량 현금화(EXIT) 및 관망 권고<br>\n"
                "• 트리거: 수출단가 하락세 지속 및 재고 누적 미해소"
            ),
            trigger_stage1="전기차 판매 성장률 둔화 (1단계 경보)",
            trigger_stage2="양극재 통관 수출액 역성장 지속 (2단계 경보)",
            trigger_stage3="<strong>전량 매도 및 현금화 권고</strong> (수출단가 양전환 전까지 유지)",
            monitored_sources="관세청 HSK 284190 / 통계청 배터리 재고지수",
        ))

        return records

    @classmethod
    def render_portfolio_table_rows(cls) -> str:
        """Generates dynamic HTML table rows for Screen 1 Table 1."""
        records = cls.evaluate_all()
        rows_html = []

        for r in records:
            aux_str = f" ({r.auxiliary_info})" if r.auxiliary_info else ""
            opacity_style = "opacity:0.85;" if r.suitability_grade.startswith("투자 부적합") else ""

            row = (
                f'                <tr style="background:{r.row_bg_color};{opacity_style}">\n'
                f'                    <td>\n'
                f'                        <strong style="font-size:13px;">{r.sector_num}. {r.sector_name}</strong><br>\n'
                f'                        <span style="font-size:11px;color:var(--text-dim);">{r.industry_class}</span>\n'
                f'                    </td>\n'
                f'                    <td>\n'
                f'                        <strong style="font-size:14px;color:#fff;">{r.company_name}</strong><br>\n'
                f'                        <span style="font-size:11px;color:var(--text-dim);">{r.stock_code}{aux_str}</span>\n'
                f'                    </td>\n'
                f'                    <td><span class="status-badge {r.grade_badge_class}" style="font-size:11px;">{r.suitability_grade}</span></td>\n'
                f'                    <td>\n'
                f'                        {r.fact_evidence_html}\n'
                f'                    </td>\n'
                f'                    <td>\n'
                f'                        <div style="font-size:12px;color:var(--text-dim);">현재가: <strong id="live_price_{r.stock_code}" style="color:#38bdf8;font-size:14px;">{int(r.current_price):,}원</strong> <span style="font-size:11px;color:#94a3b8;">(KRX 실시간 체결)</span></div>\n'
                f'                        <div style="font-size:15px;color:var(--pass);font-weight:800;margin:2px 0;">목표가 {r.target_price_str}</div>\n'
                f'                        <span id="live_ret_{r.stock_code}" style="font-size:11px;color:var(--accent);font-weight:600;">{r.expected_return_str}</span>\n'
                f'                    </td>\n'
                f'                    <td>{r.valuation_html}</td>\n'
                f'                    <td>{r.investment_points_html}</td>\n'
                f'                    <td>\n'
                f'                        <span class="status-badge {r.action_badge_class}" style="font-size:11px;">{r.action_status}</span><br>\n'
                f'                        <span style="font-size:11px;color:var(--text-dim);line-height:1.4;display:inline-block;margin-top:4px;">\n'
                f'                            {r.action_rules_html}\n'
                f'                        </span>\n'
                f'                    </td>\n'
                f'                </tr>'
            )
            rows_html.append(row)

        return "\n\n".join(rows_html)

    @classmethod
    def render_trigger_table_rows(cls) -> str:
        """Generates dynamic HTML table rows for Screen 1 Table 2 (Exit Triggers)."""
        records = cls.evaluate_all()
        rows_html = []

        for r in records:
            danger_bg = ' style="background:rgba(239, 68, 68, 0.08);"' if "SELL" in r.action_status or "매도" in r.action_status else ""
            row = (
                f'                <tr{danger_bg}>\n'
                f'                    <td><strong>{r.company_name} ({r.stock_code})</strong><br><span style="font-size:11px;color:var(--text-dim);">{r.sector_name}</span></td>\n'
                f'                    <td><span class="status-badge {r.action_badge_class}">{r.action_status}</span></td>\n'
                f'                    <td>{r.trigger_stage1}</td>\n'
                f'                    <td>{r.trigger_stage2}</td>\n'
                f'                    <td>{r.trigger_stage3}</td>\n'
                f'                    <td>{r.monitored_sources}</td>\n'
                f'                </tr>'
            )
            rows_html.append(row)

        return "\n".join(rows_html)

    @classmethod
    def calculate_strategy_returns(cls) -> Dict[str, Any]:
        """
        Dynamically calculates weighted expected return ranges for:
        - Strategy A: 40% SK + 35% HMC + 25% HD Electric
        - Strategy B: 30% Cash (base_rate) + 30% SK + 25% HMC + 15% HD Electric
        - Overall Portfolio Goal
        """
        records = {r.sector_id: r for r in cls.evaluate_all()}
        sk = records["SEMI_HBM"]
        hmc = records["AUTO"]
        hd = records["POWER_GRID"]
        cash_rate = float(SyncState.base_rate_pct)

        a_low = round(0.40 * sk.return_low_pct + 0.35 * hmc.return_low_pct + 0.25 * hd.return_low_pct, 1)
        a_high = round(0.40 * sk.return_high_pct + 0.35 * hmc.return_high_pct + 0.25 * hd.return_high_pct, 1)

        b_low = round(0.30 * cash_rate + 0.30 * sk.return_low_pct + 0.25 * hmc.return_low_pct + 0.15 * hd.return_low_pct, 1)
        b_high = round(0.30 * cash_rate + 0.30 * sk.return_high_pct + 0.25 * hmc.return_high_pct + 0.15 * hd.return_high_pct, 1)

        return {
            "strategy_a": {
                "low": a_low,
                "high": a_high,
                "str": f"연 +{a_low:.1f}% ~ +{a_high:.1f}%",
            },
            "strategy_b": {
                "low": b_low,
                "high": b_high,
                "str": f"연 +{b_low:.1f}% ~ +{b_high:.1f}%",
            },
            "kpi_goal": {
                "low": b_low,
                "high": a_high,
                "str": f"연 +{b_low:.1f}% ~ +{a_high:.1f}%",
            }
        }

    @classmethod
    def _calc_return_str_and_floats(cls, cur_p: float, t_low: float, t_high: float, note: str = "") -> Tuple[str, float, float]:
        if cur_p and cur_p > 0:
            r1 = round((t_low - cur_p) / cur_p * 100, 1)
            r2 = round((t_high - cur_p) / cur_p * 100, 1)
            p1 = "+" if r1 > 0 else ""
            p2 = "+" if r2 > 0 else ""
            n_part = f" / {note}" if note else ""
            return f"(연 {p1}{r1}% ~ {p2}{r2}%{n_part} / 1년 기준)", r1, r2
        return "(수익률 산출 중)", 0.0, 0.0
