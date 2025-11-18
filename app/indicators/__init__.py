"""Indicators module."""

# Import from indicators.py module file
import sys
from pathlib import Path
import importlib.util

parent_app = Path(__file__).parent.parent
indicators_module_path = parent_app / "indicators.py"

if indicators_module_path.exists():
    spec = importlib.util.spec_from_file_location("indicators_module", indicators_module_path)
    indicators_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indicators_module)
    
    RsiCalculator = indicators_module.RsiCalculator
    
    __all__ = ["RsiCalculator"]
else:
    __all__ = []

