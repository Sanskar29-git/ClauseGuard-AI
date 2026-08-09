from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
MAX_FILE_SIZE = 20 * 1024 * 1024

PRIORITIES = {
    "balanced": {"financial":1.0,"termination":1.0,"renewal":.9,"liability":1.0,"restrictions":.8,"privacy":.7,"ip":.7,"disputes":.7,"obligations":.8},
    "cost": {"financial":1.6,"termination":.8,"renewal":.9,"liability":1.1,"restrictions":.5,"privacy":.4,"ip":.4,"disputes":.5,"obligations":.7},
    "flexibility": {"financial":.7,"termination":1.7,"renewal":1.5,"liability":.8,"restrictions":1.4,"privacy":.4,"ip":.4,"disputes":.7,"obligations":.9},
    "security": {"financial":1.0,"termination":.8,"renewal":.6,"liability":1.5,"restrictions":.7,"privacy":1.5,"ip":1.3,"disputes":1.1,"obligations":1.0},
    "business": {"financial":1.2,"termination":1.2,"renewal":1.0,"liability":1.4,"restrictions":.9,"privacy":1.0,"ip":1.3,"disputes":1.1,"obligations":1.0},
}
