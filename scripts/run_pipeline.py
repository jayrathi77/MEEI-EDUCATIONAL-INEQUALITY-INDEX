"""
Master Pipeline Runner
=======================
Executes all pipeline steps in dependency order.
Run: python run_pipeline.py
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).parent
SYNTHETIC_GEN = Path(__file__).parent.parent / "data" / "synthetic_demo" / "generate_synthetic_data.py"

STEPS = [
    ("Generate Synthetic Demo Data", str(SYNTHETIC_GEN)),
    ("Build MEEI Index",             str(SCRIPTS_DIR / "build_meei.py")),
    ("Estimate IOp",                 str(SCRIPTS_DIR / "estimate_iop.py")),
    ("Train Predictive Models",      str(SCRIPTS_DIR / "train_models.py")),
    ("Generate SHAP Explanations",   str(SCRIPTS_DIR / "generate_explanations.py")),
    ("Build Priority Districts",     str(SCRIPTS_DIR / "build_priority_list.py")),
]


def run_step(name: str, script: str) -> bool:
    logger.info("=" * 60)
    logger.info("STEP: %s", name)
    logger.info("Script: %s", script)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run([sys.executable, script], capture_output=False, env=env)
    if result.returncode != 0:
        logger.error("FAILED: %s (exit code %d)", name, result.returncode)
        return False
    logger.info("OK: %s", name)
    return True


def main():
    print("\n" + "=" * 60)
    print("  MEEI PIPELINE -- SYNTHETIC DEMO MODE")
    print("  All outputs are demo data. Not real research results.")
    print("=" * 60 + "\n")

    for name, script in STEPS:
        if not run_step(name, script):
            logger.error("Pipeline aborted at: %s", name)
            sys.exit(1)

    logger.info("Pipeline complete. Start backend: uvicorn backend.app.main:app --reload")


if __name__ == "__main__":
    main()
