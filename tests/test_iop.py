"""Unit tests for Inequality of Opportunity (IOp) estimation."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from estimate_iop import gini, estimate_iop


def test_gini_bounds():
    # Perfectly equal distribution -> Gini = 0
    equal = np.ones(100)
    assert np.isclose(gini(equal), 0.0, atol=1e-5)

    # Standard skewed distribution
    skewed = np.array([1, 1, 1, 1, 100])
    g = gini(skewed)
    assert 0.0 < g < 1.0


def test_estimate_iop_pipeline():
    processed_parquet = Path(__file__).parent.parent / "data" / "processed" / "districts_demo.parquet"
    if not processed_parquet.exists():
        pytest.skip("Synthetic demo data not found")

    df = pd.read_parquet(processed_parquet)
    result = estimate_iop(df)

    assert result["status"] == "OK"
    assert 0.0 <= result["gini_overall"] <= 1.0
    assert 0.0 <= result["gini_predicted_types"] <= 1.0
    assert 0.0 <= result["iop_relative"] <= 1.0
    assert "circumstance_importance" in result
    assert len(result["circumstance_importance"]) > 0
