from fastapi import APIRouter
from app.services.data_service import data_service
import json
from pathlib import Path
from app.core.config import settings

router = APIRouter()
DIAG_PATH = settings.models_dir / "index" / "meei_diagnostics.json"


@router.get("/index/summary")
def index_summary():
    meei = data_service.meei
    if meei is None:
        return {"status": "NO_DATA"}
    valid = meei.dropna(subset=["meei"])
    dist = valid["meei"].describe().round(4).to_dict()
    return {
        "n_districts": len(valid),
        "distribution": dist,
        "sub_indices": {
            col: valid[col].describe().round(4).to_dict()
            for col in ["perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]
            if col in valid.columns
        },
        "data_source": "NAS_UDISE_HARMONIZED",
    }


@router.get("/index/diagnostics")
def index_diagnostics():
    if not DIAG_PATH.exists():
        return {"status": "NO_DIAGNOSTICS", "message": "Run build_meei.py first."}
    with open(DIAG_PATH) as f:
        diag = json.load(f)
    return diag
