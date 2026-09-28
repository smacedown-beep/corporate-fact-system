"""Source package for Corporate Investment FACT System."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Self-alias
if 'corporate_invest_system_next' not in sys.modules:
    import types
    mod = types.ModuleType('corporate_invest_system_next')
    mod.__file__ = str(_ROOT / '__init__.py')
    mod.__path__ = [str(_ROOT)]
    sys.modules['corporate_invest_system_next'] = mod
