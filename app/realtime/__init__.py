"""Real-time monitoring module."""

# Import from the realtime.py module file (not this package)
import sys
from pathlib import Path

# Import from parent module
parent_app = Path(__file__).parent.parent
realtime_module_path = parent_app / "realtime.py"

if realtime_module_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("realtime_module", realtime_module_path)
    realtime_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(realtime_module)
    
    run_realtime_monitor = realtime_module.run_realtime_monitor
    RealtimeMonitor = realtime_module.RealtimeMonitor
    
    __all__ = ["run_realtime_monitor", "RealtimeMonitor"]
else:
    # Fallback: try direct import
    from app.realtime import run_realtime_monitor, RealtimeMonitor
    __all__ = ["run_realtime_monitor", "RealtimeMonitor"]

