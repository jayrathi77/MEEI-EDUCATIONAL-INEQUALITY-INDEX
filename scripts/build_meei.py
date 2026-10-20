"""
MEEI Construction Pipeline
===========================
Implements the two-stage PCA methodology described in the paper.

Stage 1: Four group sub-indices (P, I, E, C)
  - Standardise indicators
  - KMO + Bartlett suitability checks
  - PCA with eigenvalue > 1 retention
  - Varimax rotation
  - Variance-weighted sub-index scores
  - Min-max rescale to [0, 1]

Stage 2: Second PCA on the four sub-indices → MEEI

All decisions are logged and a diagnostics artefact is saved.
"""

import json
import logging
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=RuntimeWarning)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).parent.parent / "models" / "index"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Utility: KMO and Bartlett
# ─────────────────────────────────────────────────────────────────────────────

def kmo_measure(corr_matrix: np.ndarray) -> float:
    """Kaiser–Meyer–Olkin adequacy measure."""
    corr = corr_matrix.copy()
    np.fill_diagonal(corr, 0)
    partial_corr = -np.linalg.pinv(corr_matrix)
    np.fill_diagonal(partial_corr, 0)
    num = np.sum(corr ** 2)
    denom = np.sum(corr ** 2) + np.sum(partial_corr ** 2)
    return float(num / denom) if denom > 0 else 0.0


def bartlett_sphericity(data: np.ndarray):
    """Bartlett's test of sphericity."""
    n, p = data.shape
    corr = np.corrcoef(data, rowvar=False)
    det = np.linalg.det(corr)
    det = max(det, 1e-12)
    chi_sq = -(n - 1 - (2 * p + 5) / 6) * np.log(det)
    df = p * (p - 1) / 2
    p_val = 1 - chi2.cdf(chi_sq, df)
    return float(chi_sq), int(df), float(p_val)


# ─────────────────────────────────────────────────────────────────────────────
# Varimax rotation
# ─────────────────────────────────────────────────────────────────────────────

def varimax(loadings: np.ndarray, max_iter: int = 1000, tol: float = 1e-6) -> np.ndarray:
    """Analytic Varimax rotation."""
    p, k = loadings.shape
    if k == 1:
        return loadings
    rot = np.eye(k)
    for _ in range(max_iter):
        old_rot = rot.copy()
        for i in range(k):
            for j in range(i + 1, k):
                u = loadings[:, i] ** 2 - loadings[:, j] ** 2
                v = 2 * loadings[:, i] * loadings[:, j]
                A = np.sum(u)
                B = np.sum(v)
                C = np.sum(u ** 2 - v ** 2)
                D = 2 * np.sum(u * v)
                num = D - 2 * A * B / p
                den = C - (A ** 2 - B ** 2) / p
                angle = 0.25 * np.arctan2(num, den)
                rot_ij = np.eye(k)
                rot_ij[i, i] = np.cos(angle)
                rot_ij[j, j] = np.cos(angle)
                rot_ij[i, j] = -np.sin(angle)
                rot_ij[j, i] = np.sin(angle)
                loadings = loadings @ rot_ij
                rot = rot @ rot_ij
        if np.max(np.abs(rot - old_rot)) < tol:
            break
    return loadings


# ─────────────────────────────────────────────────────────────────────────────
# Sub-index builder
# ─────────────────────────────────────────────────────────────────────────────

def build_subindex(
    data: pd.DataFrame,
    cols: list[str],
    group_label: str,
    flip_higher_is_worse: Optional[list[str]] = None,
    min_obs: int = 10,
) -> dict:
    """
    Build one sub-index using PCA with eigenvalue>1 criterion and Varimax.

    Returns a dict with:
        scores: pd.Series aligned to data.index
        diagnostics: dict of methodological metadata
    """
    flip_higher_is_worse = flip_higher_is_worse or []
    diag = {"group": group_label, "columns": cols}

    # ── Select available columns and drop rows with all-NaN ─────────────────
    avail = [c for c in cols if c in data.columns]
    if len(avail) < 2:
        logger.warning("%s: fewer than 2 available columns (%s). Skipping.", group_label, avail)
        diag["status"] = "SKIPPED_INSUFFICIENT_COLUMNS"
        return {"scores": pd.Series(np.nan, index=data.index), "diagnostics": diag}

    sub = data[avail].copy()
    # Flip so higher always means better
    for col in flip_higher_is_worse:
        if col in sub.columns:
            sub[col] = -sub[col]

    # Drop rows where >50 % of indicators are missing
    thresh = len(avail) // 2
    sub = sub.dropna(thresh=max(thresh, 1))
    valid_idx = sub.index

    if len(valid_idx) < min_obs:
        logger.warning("%s: only %d valid rows. Skipping.", group_label, len(valid_idx))
        diag["status"] = "SKIPPED_TOO_FEW_OBSERVATIONS"
        return {"scores": pd.Series(np.nan, index=data.index), "diagnostics": diag}

    # ── Impute remaining NaN with column median (within valid rows) ──────────
    sub = sub.apply(lambda col: col.fillna(col.median()))

    # ── Standardise ─────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X = scaler.fit_transform(sub.values)

    if X.shape[1] < 2:
        diag["status"] = "SKIPPED_SINGLE_COLUMN"
        return {"scores": pd.Series(np.nan, index=data.index), "diagnostics": diag}

    # ── KMO and Bartlett ────────────────────────────────────────────────────
    corr = np.corrcoef(X, rowvar=False)
    kmo = kmo_measure(corr)
    chi_sq, df_b, p_b = bartlett_sphericity(X)
    diag["kmo"] = round(kmo, 4)
    diag["bartlett_chi2"] = round(chi_sq, 4)
    diag["bartlett_p"] = round(p_b, 6)

    if kmo < 0.50 and p_b > 0.05:
        logger.warning("%s: KMO=%.3f < 0.50 and Bartlett p=%.4f > 0.05. PCA may be unreliable.", group_label, kmo, p_b)
        diag["pca_suitability_warning"] = "KMO < 0.50 and Bartlett non-significant. Results should be interpreted cautiously."

    # ── PCA ─────────────────────────────────────────────────────────────────
    pca_full = PCA()
    pca_full.fit(X)
    eigenvalues = pca_full.explained_variance_
    retained = int(np.sum(eigenvalues > 1.0))
    if retained == 0:
        retained = 1  # always keep at least one
    diag["eigenvalues"] = [round(e, 4) for e in eigenvalues]
    diag["retained_components"] = retained
    diag["explained_variance_ratios"] = [round(v, 4) for v in pca_full.explained_variance_ratio_[:retained]]
    diag["total_explained_variance"] = round(float(np.sum(pca_full.explained_variance_ratio_[:retained])), 4)

    # ── Apply Varimax ────────────────────────────────────────────────────────
    raw_loadings = pca_full.components_[:retained].T  # shape (p, k)
    rotated_loadings = varimax(raw_loadings)
    diag["rotated_loadings"] = {avail[i]: [round(v, 4) for v in rotated_loadings[i]] for i in range(len(avail))}

    # ── Compute factor scores from rotated solution ──────────────────────────
    # Project X onto rotated loadings using regression method
    scores_mat = X @ rotated_loadings  # shape (n, k)

    # ── Variance-weighted sub-index (Paper equation) ──────────────────────────
    retained_ev = eigenvalues[:retained]
    weights = retained_ev / retained_ev.sum()
    diag["component_weights"] = [round(w, 4) for w in weights]
    S = scores_mat @ weights  # weighted combination

    # ── Min–max rescale to [0, 1] ────────────────────────────────────────────
    s_min, s_max = S.min(), S.max()
    diag["raw_score_min"] = round(float(s_min), 4)
    diag["raw_score_max"] = round(float(s_max), 4)

    if np.isclose(s_min, s_max):
        logger.warning("%s: zero range after PCA. All districts have identical score.", group_label)
        diag["status"] = "WARNING_ZERO_RANGE"
        I_scaled = np.full_like(S, 0.5)
    else:
        I_scaled = (S - s_min) / (s_max - s_min)

    diag["status"] = "OK"

    out = pd.Series(np.nan, index=data.index)
    out.loc[valid_idx] = I_scaled
    return {"scores": out, "diagnostics": diag}


# ─────────────────────────────────────────────────────────────────────────────
# Main MEEI builder
# ─────────────────────────────────────────────────────────────────────────────

PERFORMANCE_COLS = [
    "nas_math_cl3", "nas_lang_cl3",
    "nas_math_cl5", "nas_lang_cl5",
    "nas_math_cl8", "nas_lang_cl8",
]

INFRASTRUCTURE_COLS = [
    "pct_schools_electricity", "pct_schools_drinking_water",
    "pct_schools_toilets", "pct_schools_computers",
    "pct_schools_library", "pct_schools_permanent_building",
    "pct_schools_medical_checkup",
]

# Higher pupil-teacher ratio is WORSE → flip
INFRASTRUCTURE_FLIP = ["pupil_teacher_ratio"]

# Equity: gaps. Larger gap = worse equity → flip all
EQUITY_COLS = [
    "gender_gap_math_cl5", "gender_gap_lang_cl5",
    "rural_urban_gap_math", "sc_gap_math_cl5", "st_gap_math_cl5",
]
EQUITY_FLIP = EQUITY_COLS  # all gaps: larger magnitude = more inequity

CIRCUMSTANCE_COLS = [
    "pct_literate_parents", "pct_urban_hh",
    "pct_professional_occupation", "hdi_proxy",
]
# pct_sc_st is not necessarily bad; note in methodology
CIRCUMSTANCE_FLIP: list[str] = []


def build_meei(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Compute MEEI for all districts in df.
    Returns (results_df, diagnostics_dict).
    """
    diag_all = {}

    res_P = build_subindex(df, PERFORMANCE_COLS, "Performance")
    res_I = build_subindex(df, INFRASTRUCTURE_COLS + ["pupil_teacher_ratio"], "Infrastructure",
                           flip_higher_is_worse=INFRASTRUCTURE_FLIP)
    res_E = build_subindex(df, EQUITY_COLS, "Equity", flip_higher_is_worse=EQUITY_FLIP)
    res_C = build_subindex(df, CIRCUMSTANCE_COLS, "Circumstances", flip_higher_is_worse=CIRCUMSTANCE_FLIP)

    diag_all["Performance"] = res_P["diagnostics"]
    diag_all["Infrastructure"] = res_I["diagnostics"]
    diag_all["Equity"] = res_E["diagnostics"]
    diag_all["Circumstances"] = res_C["diagnostics"]

    sub_df = pd.DataFrame({
        "perf_subindex": res_P["scores"],
        "infra_subindex": res_I["scores"],
        "equity_subindex": res_E["scores"],
        "circ_subindex": res_C["scores"],
    })

    # ── Stage 2: Second PCA on four sub-indices ───────────────────────────
    stage2_avail = sub_df.dropna()
    valid2_idx = stage2_avail.index

    meei_series = pd.Series(np.nan, index=df.index)

    if len(valid2_idx) >= 10 and stage2_avail.shape[1] >= 2:
        X2 = StandardScaler().fit_transform(stage2_avail.values)
        pca2 = PCA(n_components=1)
        pca2.fit(X2)
        scores2 = pca2.transform(X2).ravel()
        s_min2, s_max2 = scores2.min(), scores2.max()
        if not np.isclose(s_min2, s_max2):
            meei_raw = (scores2 - s_min2) / (s_max2 - s_min2)
        else:
            meei_raw = np.full_like(scores2, 0.5)

        meei_series.loc[valid2_idx] = meei_raw

        # Orientation check: MEEI should correlate positively with performance
        # If PC1 loads negatively on performance subindex, flip sign
        perf_loading = pca2.components_[0][list(stage2_avail.columns).index("perf_subindex")]
        if perf_loading < 0:
            meei_series = 1 - meei_series
            logger.info("Flipped MEEI sign so that higher = better performance.")

        diag_all["MEEI_stage2"] = {
            "status": "OK",
            "n_districts": len(valid2_idx),
            "pc1_loadings": {c: round(v, 4) for c, v in zip(stage2_avail.columns, pca2.components_[0])},
            "explained_variance_ratio": round(float(pca2.explained_variance_ratio_[0]), 4),
            "orientation_check": {"perf_loading": round(float(perf_loading), 4),
                                   "flipped": perf_loading < 0},
        }
    else:
        diag_all["MEEI_stage2"] = {"status": "INSUFFICIENT_DATA"}
        logger.warning("Stage 2 PCA could not run: insufficient valid sub-index rows.")

    # ── Assemble results ─────────────────────────────────────────────────
    result = df[["district_id", "district_name", "state_name"]].copy()
    result = result.join(sub_df)
    result["meei"] = meei_series

    # Rank (higher MEEI = better equality rank = 1)
    result["meei_rank"] = result["meei"].rank(ascending=False, method="min")
    result["is_synthetic"] = df.get("is_synthetic", pd.Series(False, index=df.index))

    return result, diag_all


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
    parquet_path = PROCESSED_DIR / "districts_demo.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Processed data not found at {parquet_path}. Run generate_synthetic_data.py first.")

    df = pd.read_parquet(parquet_path)
    logger.info("Loaded %d districts from %s", len(df), parquet_path)

    result, diag = build_meei(df)

    result.to_parquet(PROCESSED_DIR / "meei_results.parquet", index=False)
    result.to_csv(PROCESSED_DIR / "meei_results.csv", index=False)

    with open(MODELS_DIR / "meei_diagnostics.json", "w") as f:
        json.dump(diag, f, indent=2, default=_json_default)

    logger.info("MEEI computed for %d districts.", result["meei"].notna().sum())
    logger.info("Saved -> meei_results.parquet, meei_diagnostics.json")
    print(result[["district_name", "state_name", "meei", "meei_rank"]].dropna().sort_values("meei_rank").head(15))


if __name__ == "__main__":
    run()
