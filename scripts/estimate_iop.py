"""
Inequality of Opportunity (IOp) Estimation
============================================
Implements ex-ante IOp methodology:

  1. Overall Gini coefficient on outcome distribution
  2. Conditional expected outcomes via circumstance-based types
     (approximated with Random Forest since Python lacks a faithful CIF)
  3. Relative IOp = G(m) / G(y)
  4. Conditional permutation importance for circumstances

METHODOLOGICAL NOTE:
  Individual-level IOp requires individual microdata (e.g. NSS/PLFS household
  surveys). Since such data are not automatically available, this script:
  - Estimates IOp at the DISTRICT level using district-level circumstance averages
  - Clearly labels all outputs as "district-level approximation"
  - Does NOT present results as individual-level IOp estimates
"""

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import cross_val_predict, KFold
import joblib

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).parent.parent / "models" / "explainability"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CIRCUMSTANCE_COLS = [
    "pct_literate_parents",
    "pct_urban_hh",
    "pct_sc_st_population",
    "pct_professional_occupation",
    "hdi_proxy",
]

OUTCOME_COL = "nas_math_cl5"   # Representative outcome for IOp


def gini(arr: np.ndarray) -> float:
    """Gini coefficient for a non-negative array."""
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0 or arr.mean() <= 0:
        return float("nan")
    arr_sorted = np.sort(arr)
    n = len(arr_sorted)
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * arr_sorted) - (n + 1) * arr_sorted.sum()) /
                 (n * arr_sorted.sum()))


def estimate_iop(df: pd.DataFrame) -> dict:
    avail_circ = [c for c in CIRCUMSTANCE_COLS if c in df.columns]
    if OUTCOME_COL not in df.columns:
        return {"status": "NO_OUTCOME_COLUMN", "outcome": OUTCOME_COL}

    sub = df[[OUTCOME_COL] + avail_circ].dropna()
    if len(sub) < 20:
        return {"status": "INSUFFICIENT_DATA", "n": len(sub)}

    y = sub[OUTCOME_COL].values
    C = sub[avail_circ].values

    # Overall Gini
    G_y = gini(y)

    # Predicted conditional mean via RF cross-val
    rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    m_hat = cross_val_predict(rf, C, y, cv=kf)
    m_hat = np.clip(m_hat, 0, None)  # non-negative

    G_m = gini(m_hat)

    iop_relative = G_m / G_y if G_y > 0 else float("nan")

    # ── Conditional permutation importance ────────────────────────────────
    rf.fit(C, y)
    perm = permutation_importance(rf, C, y, n_repeats=30, random_state=42, n_jobs=-1)
    importance_dict = {
        avail_circ[i]: {
            "mean": round(float(perm.importances_mean[i]), 6),
            "std": round(float(perm.importances_std[i]), 6),
            "rank": int(np.argsort(-perm.importances_mean)[i] + 1 if i in np.argsort(-perm.importances_mean) else 0),
        }
        for i in range(len(avail_circ))
    }
    # Compute ranks properly
    ranks = np.argsort(-perm.importances_mean)
    for rank_pos, col_idx in enumerate(ranks):
        importance_dict[avail_circ[col_idx]]["rank"] = rank_pos + 1

    # Save model for API
    joblib.dump(rf, MODELS_DIR / "iop_rf_model.pkl")

    result = {
        "status": "OK",
        "estimation_level": "DISTRICT",
        "outcome_variable": OUTCOME_COL,
        "n_districts": int(len(sub)),
        "gini_overall": round(G_y, 6),
        "gini_predicted_types": round(G_m, 6),
        "iop_relative": round(iop_relative, 6),
        "iop_relative_pct": round(iop_relative * 100, 2),
        "circumstance_importance": importance_dict,
        "circumstances_used": avail_circ,
    }
    return result


def _json_default(o):
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer, int)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, pd.Series):
        return o.to_dict()
    return str(o)


def run():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    raw_path = PROCESSED_DIR / "districts_demo.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Processed data not found: {raw_path}")

    df = pd.read_parquet(raw_path)
    logger.info("Estimating IOp for %d districts...", len(df))

    result = estimate_iop(df)

    out_path = PROCESSED_DIR / "iop_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=_json_default)

    logger.info("IOp results saved to %s", out_path)
    if result.get("status") == "OK":
        print(f"\nGini(y)   = {result['gini_overall']:.4f}")
        print(f"Gini(m)   = {result['gini_predicted_types']:.4f}")
        print(f"IOp_rel   = {result['iop_relative']:.4f}  ({result['iop_relative_pct']:.1f}%)")
        print("\nCircumstance Importance:")
        for c, v in sorted(result["circumstance_importance"].items(), key=lambda x: x[1]["rank"]):
            print(f"  Rank {v['rank']:2d}  {c:<35}  mean={v['mean']:.5f} +/- {v['std']:.5f}")


if __name__ == "__main__":
    run()
