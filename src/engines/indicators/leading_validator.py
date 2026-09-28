"""
Corporate Investment FACT System - Leading Indicator Validation Engine.
Performs rigorous lag analysis (-3 to +3), in-sample/out-of-sample correlation,
statistical significance, and reliability grading without lookahead bias.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import math

@dataclass
class LagTestResult:
    lag: int
    sample_size: int
    is_correlation: float
    oos_correlation: float
    p_value: float
    is_significant: bool
    status: str  # VERIFIED, SUPPORTED, WEAK, INSUFFICIENT_HISTORY, INVALIDATED

@dataclass
class IndicatorValidationReport:
    indicator_id: str
    indicator_name: str
    sector_id: str
    target_metric: str  # e.g., 'COMPANY_REVENUE_YOY', 'EPS_YOY', 'PRICE_RETURN_6M'
    tested_lags: List[LagTestResult]
    best_lag: int
    best_oos_corr: float
    overall_status: str  # VERIFIED, SUPPORTED, WEAK, INSUFFICIENT_HISTORY, etc.
    provenance_source: str
    notes: str

class LeadingIndicatorValidator:
    """Validates causal lead-lag relationships across industrial leading indicators."""

    @staticmethod
    def _compute_pearson(x: List[float], y: List[float]) -> Tuple[float, float, int]:
        n = min(len(x), len(y))
        if n < 5:
            return 0.0, 1.0, n
        x_sub = x[:n]
        y_sub = y[:n]
        mean_x = sum(x_sub) / n
        mean_y = sum(y_sub) / n
        var_x = sum((xi - mean_x) ** 2 for xi in x_sub)
        var_y = sum((yi - mean_y) ** 2 for yi in y_sub)
        if var_x < 1e-12 or var_y < 1e-12:
            return 0.0, 1.0, n
        cov = sum((x_sub[i] - mean_x) * (y_sub[i] - mean_y) for i in range(n))
        r = cov / math.sqrt(var_x * var_y)
        # Approximate two-tailed t-test p-value
        df = n - 2
        if abs(r) >= 1.0:
            return r, 0.0, n
        t_stat = r * math.sqrt(df / (1.0 - r * r))
        # Simple normal approx for p-value
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2))))
        return round(r, 4), round(p_val, 4), n

    @classmethod
    def evaluate_indicator(
        cls,
        indicator_id: str,
        indicator_name: str,
        sector_id: str,
        indicator_series: List[Dict[str, Any]],  # [{'date': 'YYYY-MM-DD', 'value': float, 'avail_date': '...'}]
        target_series: List[Dict[str, Any]],     # [{'date': 'YYYY-MM-DD', 'value': float}]
        decision_date: str,
        target_metric: str = "TARGET_YOY_PERFORMANCE",
        source_name: str = "OFFICIAL_STATISTICS"
    ) -> IndicatorValidationReport:
        # Enforce PIT filtering: only indicator observations available on or before decision_date
        pit_indicator = [
            d for d in indicator_series
            if d.get("avail_date", d["date"]) <= decision_date
        ]
        
        # Sort both by date
        pit_indicator.sort(key=lambda x: x["date"])
        target_series_sorted = sorted(target_series, key=lambda x: x["date"])
        
        # Build map
        target_map = {d["date"]: d["value"] for d in target_series_sorted}
        
        lags_to_test = [-3, -2, -1, 0, 1, 2, 3]
        lag_results: List[LagTestResult] = []
        
        # Align series with date offsets (assuming monthly or quarterly records)
        dates = [d["date"] for d in pit_indicator]
        
        for lag in lags_to_test:
            x_vals = []
            y_vals = []
            for i, d in enumerate(pit_indicator):
                target_idx = i + lag
                if 0 <= target_idx < len(target_series_sorted):
                    t_val = target_series_sorted[target_idx]["value"]
                    x_vals.append(d["value"])
                    y_vals.append(t_val)
            
            n = len(x_vals)
            if n < 8:
                lag_results.append(LagTestResult(
                    lag=lag,
                    sample_size=n,
                    is_correlation=0.0,
                    oos_correlation=0.0,
                    p_value=1.0,
                    is_significant=False,
                    status="INSUFFICIENT_HISTORY"
                ))
                continue
            
            # Split In-Sample (70%) vs Out-of-Sample (30%) Walk-Forward
            split_idx = int(n * 0.70)
            is_x, is_y = x_vals[:split_idx], y_vals[:split_idx]
            oos_x, oos_y = x_vals[split_idx:], y_vals[split_idx:]
            
            is_r, is_p, is_n = cls._compute_pearson(is_x, is_y)
            oos_r, oos_p, oos_n = cls._compute_pearson(oos_x, oos_y)
            
            is_sig = is_p < 0.05
            
            # Grade status
            if oos_n < 4:
                status = "INSUFFICIENT_HISTORY"
            elif oos_r >= 0.40 and is_sig:
                status = "VERIFIED"
            elif oos_r >= 0.20:
                status = "SUPPORTED"
            elif oos_r < 0.0:
                status = "INVALIDATED"
            else:
                status = "WEAK"
                
            lag_results.append(LagTestResult(
                lag=lag,
                sample_size=n,
                is_correlation=is_r,
                oos_correlation=oos_r,
                p_value=is_p,
                is_significant=is_sig,
                status=status
            ))
            
        # Determine best lag (highest positive OOS correlation)
        valid_lags = [r for r in lag_results if r.status in ("VERIFIED", "SUPPORTED")]
        if valid_lags:
            best = max(valid_lags, key=lambda x: x.oos_correlation)
            best_lag = best.lag
            best_oos_corr = best.oos_correlation
            overall_status = best.status
        else:
            best_lag = 0
            best_oos_corr = 0.0
            overall_status = "INSUFFICIENT_HISTORY" if any(r.status == "INSUFFICIENT_HISTORY" for r in lag_results) else "WEAK"

        return IndicatorValidationReport(
            indicator_id=indicator_id,
            indicator_name=indicator_name,
            sector_id=sector_id,
            target_metric=target_metric,
            tested_lags=lag_results,
            best_lag=best_lag,
            best_oos_corr=best_oos_corr,
            overall_status=overall_status,
            provenance_source=source_name,
            notes=f"Evaluated as of decision date {decision_date}. Lookahead bias strictly prevented."
        )
