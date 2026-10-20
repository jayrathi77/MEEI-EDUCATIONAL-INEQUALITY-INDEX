from fastapi import APIRouter
from app.services.data_service import data_service
from app.core.config import settings
import pandas as pd

router = APIRouter()


@router.get("/overview")
def overview():
    meei = data_service.meei
    if meei is None:
        return {"status": "NO_DATA", "message": "Run pipeline first."}

    valid = meei.dropna(subset=["meei"])
    n_districts = len(valid)
    n_states = valid["state_name"].nunique()
    mean_meei = round(float(valid["meei"].mean()), 4)
    median_meei = round(float(valid["meei"].median()), 4)

    top5 = valid.nlargest(5, "meei")[["district_id", "district_name", "state_name", "meei", "meei_rank"]].to_dict("records")
    bottom5 = valid.nsmallest(5, "meei")[["district_id", "district_name", "state_name", "meei", "meei_rank"]].to_dict("records")

    state_avg = (
        valid.groupby("state_name")["meei"].mean().reset_index()
        .rename(columns={"meei": "avg_meei"})
        .sort_values("avg_meei", ascending=False)
        .round(4)
        .to_dict("records")
    )

    sub_avgs = {}
    for col in ["perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]:
        if col in valid.columns:
            sub_avgs[col] = round(float(valid[col].mean()), 4)

    return {
        "synthetic_mode": settings.synthetic_mode,
        "n_districts": n_districts,
        "n_states": n_states,
        "national_mean_meei": mean_meei,
        "national_median_meei": median_meei,
        "sub_index_averages": sub_avgs,
        "top5_districts": top5,
        "bottom5_districts": bottom5,
        "state_averages": state_avg,
        "data_source": "NAS_UDISE_HARMONIZED",
    }


@router.get("/coverage")
def coverage():
    meei = data_service.meei
    raw = data_service.raw
    if meei is None:
        return {"status": "NO_DATA"}

    total = len(meei)
    valid_meei = int(meei["meei"].notna().sum())
    by_state = meei.groupby("state_name").apply(
        lambda g: {"total": len(g), "with_meei": int(g["meei"].notna().sum())}
    ).to_dict()

    return {
        "total_districts": total,
        "districts_with_meei": valid_meei,
        "coverage_pct": round(valid_meei / total * 100, 1) if total else 0,
        "by_state": by_state,
        "data_source": "NAS_UDISE_HARMONIZED",
    }
