"""
SHAP Explainability Pipeline
==============================
Generates global and local SHAP explanations for the best predictive model.
Saves outputs as JSON for API consumption.
"""

import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import shap

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PREDICTIVE_DIR = Path(__file__).parent.parent / "models" / "predictive"
EXPLAIN_DIR = Path(__file__).parent.parent / "models" / "explainability"
EXPLAIN_DIR.mkdir(parents=True, exist_ok=True)

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

FEATURE_LABELS = {
    "pct_schools_electricity": "Schools with Electricity (%)",
    "pct_schools_drinking_water": "Schools with Drinking Water (%)",
    "pct_schools_toilets": "Schools with Toilets (%)",
    "pct_schools_computers": "Schools with Computers (%)",
    "pct_schools_library": "Schools with Library (%)",
    "pct_schools_permanent_building": "Schools with Permanent Building (%)",
    "pupil_teacher_ratio": "Pupil-Teacher Ratio",
    "pct_schools_medical_checkup": "Medical Check-up Coverage (%)",
    "pct_govt_schools": "Government Schools (%)",
    "pct_literate_parents": "Literate Parents (%)",
    "pct_urban_hh": "Urban Households (%)",
    "pct_sc_st_population": "SC/ST Population (%)",
    "pct_professional_occupation": "Professional Occupation (%)",
    "hdi_proxy": "HDI Proxy Score",
}


def load_artifacts():
    meta_path = PREDICTIVE_DIR / "feature_metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError("Run train_models.py first.")
    with open(meta_path) as f:
        meta = json.load(f)

    model_path = PREDICTIVE_DIR / "best_model.pkl"
    model = joblib.load(model_path)
    return model, meta


def prepare_X(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    avail = [c for c in features if c in df.columns]
    X = df[avail].fillna(df[avail].median())
    return X


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

    # Load data
    meei = pd.read_parquet(PROCESSED_DIR / "meei_results.parquet")
    raw = pd.read_parquet(PROCESSED_DIR / "districts_demo.parquet")
    df = meei.merge(
        raw[[c for c in raw.columns if c not in meei.columns or c == "district_id"]],
        on="district_id", how="left"
    )

    model, meta = load_artifacts()
    features = meta["features"]
    X = prepare_X(df, features)
    valid_mask = X.notna().all(axis=1)
    X_valid = X[valid_mask]
    df_valid = df[valid_mask].copy()

    logger.info("Computing SHAP values for %d districts...", len(X_valid))

    # ── Choose appropriate SHAP explainer ────────────────────────────────
    # Get inner estimator from pipeline
    inner = model.named_steps["model"] if hasattr(model, "named_steps") else model
    inner_type = type(inner).__name__

    if inner_type in ("RandomForestRegressor", "ExtraTreesRegressor", "GradientBoostingRegressor"):
        # Transform X through pipeline scaler first
        if hasattr(model, "named_steps") and "scaler" in model.named_steps:
            X_scaled = model.named_steps["scaler"].transform(X_valid)
        else:
            X_scaled = X_valid.values
        explainer = shap.TreeExplainer(inner)
        shap_values = explainer.shap_values(X_scaled)
        ev = explainer.expected_value
        expected_value = float(np.ravel(ev)[0]) if hasattr(ev, "__iter__") else float(ev)
    else:
        # Linear / fallback -> KernelExplainer on sample
        if hasattr(model, "named_steps") and "scaler" in model.named_steps:
            X_scaled = model.named_steps["scaler"].transform(X_valid)
        else:
            X_scaled = X_valid.values
        background = shap.kmeans(X_scaled, 10)
        explainer = shap.KernelExplainer(model.predict, background)
        shap_values = explainer.shap_values(X_scaled, nsamples=50)
        ev = explainer.expected_value
        expected_value = float(np.ravel(ev)[0]) if hasattr(ev, "__iter__") else float(ev)

    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    if hasattr(shap_values, "values"):
        shap_values = shap_values.values
    if hasattr(shap_values, "ndim") and shap_values.ndim == 3:
        shap_values = shap_values[:, :, 0]

    shap_df = pd.DataFrame(shap_values, columns=features, index=df_valid.index)

    # ── Global importance ──────────────────────────────────────────────────
    mean_abs_shap = shap_df.abs().mean().sort_values(ascending=False)
    global_importance = [
        {
            "feature": f,
            "label": FEATURE_LABELS.get(f, f),
            "mean_abs_shap": round(float(mean_abs_shap[f]), 6),
            "rank": i + 1,
        }
        for i, f in enumerate(mean_abs_shap.index)
    ]

    # ── Per-district SHAP (local) ─────────────────────────────────────────
    predictions = model.predict(X_valid)
    local_records = []
    for idx, (row_idx, row) in enumerate(df_valid.iterrows()):
        contribs = shap_df.loc[row_idx].to_dict()
        top_pos = sorted(contribs.items(), key=lambda x: x[1], reverse=True)[:5]
        top_neg = sorted(contribs.items(), key=lambda x: x[1])[:5]
        local_records.append({
            "district_id": row["district_id"],
            "district_name": row["district_name"],
            "state_name": row["state_name"],
            "predicted_equality": round(float(predictions[idx]), 4),
            "expected_value": round(expected_value, 4),
            "shap_contributions": {f: round(v, 6) for f, v in contribs.items()},
            "top_positive_drivers": [
                {"feature": f, "label": FEATURE_LABELS.get(f, f), "shap": round(v, 6)}
                for f, v in top_pos
            ],
            "top_negative_drivers": [
                {"feature": f, "label": FEATURE_LABELS.get(f, f), "shap": round(v, 6)}
                for f, v in top_neg
            ],
        })

    # ── Save outputs ──────────────────────────────────────────────────────
    global_out = {
        "model_type": inner_type,
        "expected_value": round(expected_value, 4),
        "n_districts": len(X_valid),
        "features": features,
        "global_importance": global_importance,
        "disclaimer": (
            "SHAP values describe each feature's contribution to the model prediction. "
            "They are NOT causal estimates of policy effects."
        ),
    }
    with open(EXPLAIN_DIR / "global_shap.json", "w") as f:
        json.dump(global_out, f, indent=2, default=_json_default)

    with open(EXPLAIN_DIR / "local_shap.json", "w") as f:
        json.dump(local_records, f, indent=2, default=_json_default)

    # Save index for fast lookup
    local_index = {r["district_id"]: i for i, r in enumerate(local_records)}
    with open(EXPLAIN_DIR / "local_shap_index.json", "w") as f:
        json.dump(local_index, f, indent=2, default=_json_default)

    logger.info("[OK] Global SHAP saved  -> %s", EXPLAIN_DIR / "global_shap.json")
    logger.info("[OK] Local SHAP saved   -> %s", EXPLAIN_DIR / "local_shap.json")
    print(f"\nTop 5 Global Features:")
    for item in global_importance[:5]:
        print(f"  {item['rank']}. {item['label']:<40}  mean|SHAP|={item['mean_abs_shap']:.5f}")


if __name__ == "__main__":
    run()
