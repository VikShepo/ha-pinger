"""Load the pure engine without importing Home Assistant on the developer host."""

import importlib
from pathlib import Path
import sys
import types

root = Path(__file__).resolve().parents[1]
package = types.ModuleType("pinger_under_test")
package.__path__ = [str(root / "custom_components" / "ha_pinger")]
sys.modules.setdefault("pinger_under_test", package)
model = importlib.import_module("pinger_under_test.model")
