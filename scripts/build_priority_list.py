"""
Priority District Builder
==========================
Identifies districts most in need of intervention based on:
  - Low predicted equality score (outcome-side)
  - Weakness in specific sub-indices (infrastructure, equity)
  - Model predictions with confidence measures

Documented prioritization rule:
  Priority Score = (1 - predicted_equality) × 0.5
                 + (1 - infra_subindex)     × 0.3
                 + (1 - equity_subindex)    × 0.2

Districts are ranked descending by Priority Score.
Higher priority score = greater disadvantage = needs more attention.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PREDICTIVE_DIR = Path(__file__).parent.parent / "models" / "predictive"
EXPLAIN_DIR = Path(__file__).parent.parent / "models" / "explainability"

FEATURE_COLS = [
    "pct_schools_electricity", "pct_schools_drinking_water",
    "pct_schools_toilets", "pct_schools_computers",
    "pct_schools_library", "pct_schools_permanent_building",
    "pupil_teacher_ratio", "pct_schools_medical_checkup",
    "pct_govt_schools",
    "pct_literate_parents", "pct_urban_hh",
    "pct_sc_st_population", "pct_professional_occupation",
    "hdi_proxy",
]

PRIORITY_WEIGHTS = {
    "predicted_equality": -0.5,   # lower predicted equality → higher priority
    "infra_subindex": -0.3,       # weaker infrastructure → higher priority
    "equity_subindex": -0.2,      # worse equity → higher priority
}


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

    meei = pd.read_parquet(PROCESSED_DIR / "meei_results.parquet")
    raw = pd.read_parquet(PROCESSED_DIR / "districts_demo.parquet")
    df = meei.merge(
        raw[[c for c in raw.columns if c not in meei.columns or c == "district_id"]],
        on="district_id", how="left"
    )

    meta_path = PREDICTIVE_DIR / "feature_metadata.json"
    model_path = PREDICTIVE_DIR / "best_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError("Run train_models.py first.")

    with open(meta_path) as f:
        meta = json.load(f)
    model = joblib.load(model_path)
    features = meta["features"]

    X = df[[f for f in features if f in df.columns]].fillna(
        df[[f for f in features if f in df.columns]].median()
    )
    valid_mask = X.notna().all(axis=1)
    df_valid = df[valid_mask].copy()
    X_valid = X[valid_mask]

    predictions = model.predict(X_valid)
    df_valid["predicted_equality"] = predictions

    # ── Priority Score ─────────────────────────────────────────────────────
    def safe_col(col: str) -> pd.Series:
        return df_valid[col].fillna(df_valid[col].median()) if col in df_valid.columns else pd.Series(0.5, index=df_valid.index)

    priority = (
        (1 - df_valid["predicted_equality"]) * abs(PRIORITY_WEIGHTS["predicted_equality"]) +
        (1 - safe_col("infra_subindex"))      * abs(PRIORITY_WEIGHTS["infra_subindex"]) +
        (1 - safe_col("equity_subindex"))     * abs(PRIORITY_WEIGHTS["equity_subindex"])
    )
    df_valid["priority_score"] = priority
    df_valid["priority_rank"] = priority.rank(ascending=False, method="min").astype(int)

    # Load SHAP top features per district
    local_shap_path = EXPLAIN_DIR / "local_shap.json"
    shap_by_district: dict = {}
    if local_shap_path.exists():
        with open(local_shap_path) as f:
            local_records = json.load(f)
        shap_by_district = {r["district_id"]: r for r in local_records}

    # ── Build priority table ──────────────────────────────────────────────
    records = []
    for _, row in df_valid.sort_values("priority_rank").iterrows():
        did = row["district_id"]
        shap_info = shap_by_district.get(did, {})
        rec = {
            "priority_rank": int(row["priority_rank"]),
            "district_id": did,
            "district_name": row["district_name"],
            "state_name": row["state_name"],
            "priority_score": round(float(row["priority_score"]), 4),
            "predicted_equality": round(float(row["predicted_equality"]), 4),
            "meei": round(float(row["meei"]), 4) if pd.notna(row.get("meei")) else None,
            "perf_subindex": round(float(row["perf_subindex"]), 4) if pd.notna(row.get("perf_subindex")) else None,
            "infra_subindex": round(float(row["infra_subindex"]), 4) if pd.notna(row.get("infra_subindex")) else None,
            "equity_subindex": round(float(row["equity_subindex"]), 4) if pd.notna(row.get("equity_subindex")) else None,
            "circ_subindex": round(float(row["circ_subindex"]), 4) if pd.notna(row.get("circ_subindex")) else None,
            "top_drivers": shap_info.get("top_negative_drivers", [])[:3],
            "is_synthetic": bool(row.get("is_synthetic", True)),
        }
        records.append(rec)

    # Save JSON and CSV
    with open(PROCESSED_DIR / "priority_districts.json", "w") as f:
        json.dump({
            "prioritization_rule": PRIORITY_WEIGHTS,
            "note": "Higher priority_score = greater disadvantage.",
            "districts": records,
        }, f, indent=2, default=_json_default)

    pd.DataFrame(records).to_csv(PROCESSED_DIR / "priority_districts.csv", index=False)
    logger.info("Priority list built for %d districts.", len(records))
    print("\nTop 10 Priority Districts:")
    for r in records[:10]:
        print(f"  {r['priority_rank']:3d}. {r['district_name']:<25} {r['state_name']:<20} score={r['priority_score']:.4f}")


if __name__ == "__main__":
    run()
