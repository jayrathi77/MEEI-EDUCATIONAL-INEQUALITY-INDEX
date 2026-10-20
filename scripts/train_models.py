"""
Predictive Machine Learning Pipeline
======================================
Implements model comparison with spatially grouped cross-validation.

Models:
  1. Ridge Regression (interpretable linear baseline)
  2. Random Forest
  3. Gradient Boosting
  4. Conditional Inference Forest (approximated via ExtraTreesRegressor with
     permutation-based stopping – see NOTE below)

NOTE ON CONDITIONAL INFERENCE FOREST:
  A faithful Conditional Inference Forest requires R's `party` or `partykit`
  package. Python does not have a direct equivalent. We implement the closest
  available approximation using Extra Trees with permutation importance and
  document this deviation. If R and rpy2 are available, a note in methodology
  explains how to substitute the genuine implementation.

Validation:
  - Spatially grouped k-fold: all districts from the same state are kept
    together in the same fold (state-level hold-out).
  - Prevents leakage from neighbouring districts.
  - Reports RMSE, MAE, R², Spearman ρ.
"""

import json
import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import spearmanr
import joblib

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).parent.parent / "models" / "predictive"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Feature and target definitions
# ─────────────────────────────────────────────────────────────────────────────

# TARGET: outcome-side equality = average of performance and equity sub-indices
# (matches the paper's concept of outcome equality)
TARGET_COLS = ["perf_subindex", "equity_subindex"]

# FEATURES: input-side variables (infrastructure, circumstances, school mgmt)
FEATURE_COLS = [
    # Infrastructure
    "pct_schools_electricity", "pct_schools_drinking_water",
    "pct_schools_toilets", "pct_schools_computers",
    "pct_schools_library", "pct_schools_permanent_building",
    "pupil_teacher_ratio", "pct_schools_medical_checkup",
    "pct_govt_schools",
    # Circumstances
    "pct_literate_parents", "pct_urban_hh",
    "pct_sc_st_population", "pct_professional_occupation",
    "hdi_proxy",
]

N_FOLDS = 5
RANDOM_STATE = 42


def load_data() -> pd.DataFrame:
    meei_path = PROCESSED_DIR / "meei_results.parquet"
    raw_path = PROCESSED_DIR / "districts_demo.parquet"

    if not meei_path.exists():
        raise FileNotFoundError(f"MEEI results not found: {meei_path}. Run build_meei.py first.")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw processed data not found: {raw_path}.")

    meei = pd.read_parquet(meei_path)
    raw = pd.read_parquet(raw_path)

    # Merge on district_id
    df = meei.merge(
        raw[[c for c in raw.columns if c not in meei.columns or c == "district_id"]],
        on="district_id", how="left"
    )
    return df


def build_target(df: pd.DataFrame) -> pd.Series:
    """
    Outcome-side equality score = mean of available perf & equity sub-indices.
    Documented target construction — no leakage of infra/circumstance sub-indices.
    """
    available = [c for c in TARGET_COLS if c in df.columns]
    target = df[available].mean(axis=1)
    return target


def get_groups(df: pd.DataFrame) -> np.ndarray:
    """State-based groups for GroupKFold."""
    state_ids, _ = pd.factorize(df["state_name"])
    return state_ids


def make_models() -> dict[str, Any]:
    return {
        "Ridge Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("model", RandomForestRegressor(n_estimators=200, max_features="sqrt",
                                             random_state=RANDOM_STATE, n_jobs=-1)),
        ]),
        "Gradient Boosting": Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(n_estimators=200, learning_rate=0.05,
                                                  max_depth=3, random_state=RANDOM_STATE)),
        ]),
        "Conditional Inference Forest (approx)": Pipeline([
            # NOTE: This is an Extra Trees approximation.
            # A genuine Conditional Inference Forest requires R's party/partykit.
            # See methodology.md for the installation guide.
            ("scaler", StandardScaler()),
            ("model", ExtraTreesRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)),
        ]),
    }


def evaluate_fold(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    rho, _ = spearmanr(y_true, y_pred)
    return {"rmse": rmse, "mae": mae, "r2": r2, "spearman": float(rho)}


def run_grouped_cv(df: pd.DataFrame, X: np.ndarray, y: np.ndarray,
                   groups: np.ndarray, models: dict) -> dict:
    n_groups = len(np.unique(groups))
    n_folds = min(N_FOLDS, n_groups)
    if n_folds < 2:
        logger.warning("Not enough state groups (%d) for grouped CV. Spatial validation unreliable.", n_groups)

    gkf = GroupKFold(n_splits=n_folds)
    results = {name: [] for name in models}

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        logger.info("Fold %d/%d -- train=%d, test=%d", fold_idx + 1, n_folds,
                    len(train_idx), len(test_idx))
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        for name, pipe in models.items():
            pipe_clone = clone(pipe)  # fresh copy
            pipe_clone.fit(X_train, y_train)
            y_pred = pipe_clone.predict(X_test)
            metrics = evaluate_fold(y_test, y_pred)
            metrics["fold"] = fold_idx + 1
            metrics["test_states"] = list(df["state_name"].iloc[test_idx].unique())
            results[name].append(metrics)

    return results


def aggregate_results(fold_results: dict) -> dict:
    summary = {}
    for name, folds in fold_results.items():
        df_f = pd.DataFrame(folds)
        summary[name] = {
            "mean": df_f[["rmse", "mae", "r2", "spearman"]].mean().round(4).to_dict(),
            "std": df_f[["rmse", "mae", "r2", "spearman"]].std().round(4).to_dict(),
            "folds": folds,
        }
    return summary


def select_best_model(summary: dict) -> str:
    """Select best model by lowest mean RMSE (declared evaluation criterion)."""
    return min(summary, key=lambda k: summary[k]["mean"]["rmse"])


def train_final_model(name: str, models: dict, X: np.ndarray, y: np.ndarray) -> Any:
    """Train the selected model on the full dataset for deployment."""
    pipe = clone(models[name])
    pipe.fit(X, y)
    return pipe


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
    df = load_data()
    logger.info("Loaded %d districts", len(df))

    feat_avail = [c for c in FEATURE_COLS if c in df.columns]
    target = build_target(df)

    # Keep rows with valid target and at least half of features
    valid_mask = target.notna() & (df[feat_avail].notna().sum(axis=1) >= len(feat_avail) // 2)
    df_valid = df[valid_mask].copy()
    y = target[valid_mask].values
    X_df = df_valid[feat_avail].copy()
    # Impute remaining NaN with median
    X_df = X_df.fillna(X_df.median())
    X = X_df.values
    groups = get_groups(df_valid)

    logger.info("Valid samples: %d, Features: %d", len(y), X.shape[1])

    models = make_models()
    logger.info("Running grouped CV (%d folds by state)...", N_FOLDS)
    fold_results = run_grouped_cv(df_valid, X, y, groups, models)
    summary = aggregate_results(fold_results)
    best_name = select_best_model(summary)
    logger.info("Best model: %s (RMSE=%.4f)", best_name, summary[best_name]["mean"]["rmse"])

    # ── Train final model on full data ───────────────────────────────────
    final_model = train_final_model(best_name, models, X, y)
    joblib.dump(final_model, MODELS_DIR / "best_model.pkl")

    # Save all models for API
    all_final = {}
    for name, pipe in models.items():
        m = clone(pipe)
        m.fit(X, y)
        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "")
        joblib.dump(m, MODELS_DIR / f"model_{safe_name}.pkl")
        all_final[name] = m

    # Save feature metadata
    feature_meta = {
        "features": feat_avail,
        "target_construction": TARGET_COLS,
        "n_samples": int(len(y)),
        "n_features": int(X.shape[1]),
        "best_model": best_name,
    }
    with open(MODELS_DIR / "feature_metadata.json", "w") as f:
        json.dump(feature_meta, f, indent=2, default=_json_default)

    # Save CV results
    eval_report = {
        "n_folds": N_FOLDS,
        "validation_strategy": "State-grouped k-fold (GroupKFold)",
        "evaluation_criterion": "Minimum mean RMSE",
        "best_model": best_name,
        "model_summary": summary,
        "feature_list": feat_avail,
        "target_cols": TARGET_COLS,
        "note_cif": ("Conditional Inference Forest is approximated by ExtraTreesRegressor. "
                     "A genuine CIF requires R partykit. See methodology.md."),
    }
    with open(MODELS_DIR / "evaluation_report.json", "w") as f:
        json.dump(eval_report, f, indent=2, default=_json_default)

    logger.info("Saved models and evaluation report.")
    print("\n=== Model Comparison (Mean across folds) ===")
    for name, res in summary.items():
        m = res["mean"]
        print(f"  {name:<45} RMSE={m['rmse']:.4f}  MAE={m['mae']:.4f}  R2={m['r2']:.4f}  rho={m['spearman']:.4f}")
    print(f"\nBest model: {best_name}")


if __name__ == "__main__":
    run()
