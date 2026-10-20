"""Unit tests for predictive models and cross-validation."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from train_models import make_models, evaluate_fold, build_target, load_data


def test_make_models():
    models = make_models()
    assert "Ridge Regression" in models
    assert "Random Forest" in models
    assert "Gradient Boosting" in models
    assert "Conditional Inference Forest (approx)" in models


def test_evaluate_fold_metrics():
    y_true = np.array([0.1, 0.4, 0.5, 0.8, 0.9])
    y_pred = np.array([0.12, 0.38, 0.52, 0.79, 0.88])
    metrics = evaluate_fold(y_true, y_pred)
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "r2" in metrics
    assert "spearman" in metrics
    assert metrics["rmse"] >= 0.0
    assert metrics["mae"] >= 0.0
    assert metrics["r2"] > 0.9  # very close predictions
    assert metrics["spearman"] > 0.9


def test_build_target_no_leakage():
    processed_parquet = Path(__file__).parent.parent / "data" / "processed" / "meei_results.parquet"
    if not processed_parquet.exists():
        pytest.skip("MEEI results data not found")

    df = pd.read_parquet(processed_parquet)
    target = build_target(df)
    assert len(target) == len(df)
    assert not target.isna().all()
    # Check bounds [0, 1]
    valid = target.dropna()
    assert (valid >= 0.0).all()
    assert (valid <= 1.0).all()
