from fastapi import APIRouter, HTTPException, Query
from app.services.data_service import data_service
import pandas as pd
import math

router = APIRouter()


def _merge_df() -> pd.DataFrame | None:
    meei = data_service.meei
    raw = data_service.raw
    if meei is None:
        return None
    if raw is not None:
        extra_cols = [c for c in raw.columns if c not in meei.columns or c == "district_id"]
        return meei.merge(raw[extra_cols], on="district_id", how="left")
    return meei


def _safe(val):
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
        return round(float(val), 4)
    except Exception:
        return val


@router.get("/districts")
def list_districts(
    state: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=2000),
):
    df = _merge_df()
    if df is None:
        return {"status": "NO_DATA", "districts": []}

    if state:
        df = df[df["state_name"].str.lower() == state.lower()]

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    cols = ["district_id", "district_name", "state_name", "meei", "meei_rank",
            "perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]
    avail = [c for c in cols if c in page_df.columns]

    records = []
    for _, row in page_df[avail].iterrows():
        r = {c: _safe(row[c]) if c not in ("district_id", "district_name", "state_name") else row[c] for c in avail}
        records.append(r)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "districts": records,
    }


@router.get("/districts/{district_id}")
def get_district(district_id: str):
    df = _merge_df()
    if df is None:
        raise HTTPException(404, "No data available. Run pipeline first.")

    row = df[df["district_id"] == district_id]
    if row.empty:
        raise HTTPException(404, f"District '{district_id}' not found.")

    row = row.iloc[0]
    state_name = row["state_name"]

    # State median for comparison
    state_df = df[df["state_name"] == state_name]
    state_medians = {col: _safe(state_df[col].median()) for col in
                     ["meei", "perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]
                     if col in state_df.columns}

    national_medians = {col: _safe(df[col].median()) for col in
                        ["meei", "perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]
                        if col in df.columns}

    raw_indicators = {}
    indicator_cols = [
        "nas_math_cl3", "nas_lang_cl3", "nas_math_cl5", "nas_lang_cl5",
        "nas_math_cl8", "nas_lang_cl8",
        "pct_schools_electricity", "pct_schools_drinking_water",
        "pct_schools_toilets", "pct_schools_computers",
        "pct_schools_library", "pct_schools_permanent_building",
        "pupil_teacher_ratio", "pct_schools_medical_checkup", "pct_govt_schools",
        "gender_gap_math_cl5", "rural_urban_gap_math", "sc_gap_math_cl5",
        "pct_literate_parents", "pct_urban_hh", "pct_sc_st_population",
        "pct_professional_occupation", "hdi_proxy",
    ]
    for col in indicator_cols:
        if col in row.index:
            raw_indicators[col] = _safe(row[col])

    return {
        "district_id": district_id,
        "district_name": row.get("district_name"),
        "state_name": state_name,
        "meei": _safe(row.get("meei")),
        "meei_rank": _safe(row.get("meei_rank")),
        "perf_subindex": _safe(row.get("perf_subindex")),
        "infra_subindex": _safe(row.get("infra_subindex")),
        "equity_subindex": _safe(row.get("equity_subindex")),
        "circ_subindex": _safe(row.get("circ_subindex")),
        "state_medians": state_medians,
        "national_medians": national_medians,
        "raw_indicators": raw_indicators,
        "is_synthetic": bool(row.get("is_synthetic", True)),
        "data_source": "SYNTHETIC_DEMO",
    }
