"""Portfolio and idle cash investment decision package."""
try:
    from src.engines.portfolio.suitability_evaluator import DynamicSuitabilityEvaluator, SectorSuitabilityRecord
except ImportError:
    from src.engines.portfolio.cash_allocator import DynamicSuitabilityEvaluator, SectorSuitabilityRecord
