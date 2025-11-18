"""Universe building module."""

# Import from universe.py module file
import sys
from pathlib import Path
import importlib.util

parent_app = Path(__file__).parent.parent
universe_module_path = parent_app / "universe.py"

if universe_module_path.exists():
    spec = importlib.util.spec_from_file_location("universe_module", universe_module_path)
    universe_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(universe_module)
    
    UniverseBuilder = universe_module.UniverseBuilder
    
    __all__ = ["UniverseBuilder"]
else:
    __all__ = []

