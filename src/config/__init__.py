"""Re-export Config from sibling config.py module to keep `from config import config` working
while `from config.system_prompt import ...` works via this package.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_config_module", Path(__file__).parent.parent / "config.py"
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

Config = _module.Config
config = _module.config
Environment = _module.Environment

__all__ = ["Config", "config", "Environment"]
