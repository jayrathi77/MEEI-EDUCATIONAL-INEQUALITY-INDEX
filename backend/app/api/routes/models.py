from fastapi import APIRouter
from app.services.data_service import data_service

router = APIRouter()


@router.get("/models/comparison")
def model_comparison():
    report = data_service.eval_report
    if report is None:
        return {"status": "NO_DATA", "message": "Run train_models.py first."}

    comparison = []
    for name, res in report.get("model_summary", {}).items():
        comparison.append({
            "model": name,
            "mean_rmse": res["mean"]["rmse"],
            "mean_mae": res["mean"]["mae"],
            "mean_r2": res["mean"]["r2"],
            "mean_spearman": res["mean"]["spearman"],
            "std_rmse": res["std"]["rmse"],
            "std_r2": res["std"]["r2"],
            "is_best": name == report.get("best_model"),
        })
    comparison.sort(key=lambda x: x["mean_rmse"])

    return {
        "best_model": report.get("best_model"),
        "validation_strategy": report.get("validation_strategy"),
        "evaluation_criterion": report.get("evaluation_criterion"),
        "n_folds": report.get("n_folds"),
        "note_cif": report.get("note_cif"),
        "models": comparison,
    }


@router.get("/models/validation")
def model_validation():
    report = data_service.eval_report
    if report is None:
        return {"status": "NO_DATA"}
    return {
        "feature_list": report.get("feature_list", []),
        "target_cols": report.get("target_cols", []),
        "fold_results": report.get("model_summary", {}),
    }
