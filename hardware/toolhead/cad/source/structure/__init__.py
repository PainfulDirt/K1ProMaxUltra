"""Structure parts of the K1 Max toolhead (owned by the Structure/CAD agent).

All modules work in the nozzle frame of `interfaces.py`: origin at the nozzle
tip, +X printer right, +Y printer rear, +Z up, millimetres.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]          # hardware/toolhead/cad/source
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
