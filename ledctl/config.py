import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PINS = tuple(int(p) for p in os.environ.get("LED_PINS", "17,22,24").split(","))
PWM_FREQ = int(os.environ.get("LED_PWM_FREQ", "200"))
GAMMA = float(os.environ.get("LED_GAMMA", "2.2"))
MOCK = os.environ.get("LED_MOCK", "") not in ("", "0", "false")
HOST = os.environ.get("LED_HOST", "0.0.0.0")
PORT = int(os.environ.get("LED_PORT", "5000"))
DATA_DIR = Path(os.environ.get("LED_DATA_DIR", ROOT / "data"))
