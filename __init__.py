"""Corporate Investment FACT System root package."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Self-alias for backward compatibility with corporate_invest_system_next
sys.modules['corporate_invest_system_next'] = sys.modules[__name__]
