"""Unit tests for MEEI computation and statistical checks."""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

# Ensure scripts can be imported
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from build_meei import kmo_measure, bartlett_sphericity, build_meei, varimax


def test_compute_kmo_synthetic():
    rng = np.random.default_rng(42)
    latent = rng.normal(0, 1, (100, 1))
    X = latent + rng.normal(0, 0.3, (100, 4))
    corr = np.corrcoef(X, rowvar=False)
    kmo = kmo_measure(corr)
    assert 0.0 <= kmo <= 1.0


def test_bartlett_sphericity():
    rng = np.random.default_rng(42)
    latent = rng.normal(0, 1, (100, 1))
    X = latent + rng.normal(0, 0.2, (100, 4))
    chi2, df, p_val = bartlett_sphericity(X)
    assert chi2 > 0
    assert df > 0
    assert 0.0 <= p_val <= 1.0
    # Significant correlation should have low p-value
    assert p_val < 0.05


def test_varimax_rotation():
    rng = np.random.default_rng(42)
    Phi = rng.normal(0, 1, (6, 2))
    rotated = varimax(Phi)
    assert rotated.shape == Phi.shape
    assert not np.isnan(rotated).any()


def test_build_meei_bounds_and_completeness():
    processed_parquet = Path(__file__).parent.parent / "data" / "processed" / "districts_demo.parquet"
    if not processed_parquet.exists():
        pytest.skip("Synthetic demo data not found")

    df = pd.read_parquet(processed_parquet)
    result, diag = build_meei(df)

    assert "meei" in result.columns
    assert "meei_rank" in result.columns
    valid_meei = result["meei"].dropna()
    assert len(valid_meei) > 0
    assert (valid_meei >= 0.0).all()
    assert (valid_meei <= 1.0).all()

    # Sub-indices check
    for sub in ["perf_subindex", "infra_subindex", "equity_subindex", "circ_subindex"]:
        assert sub in result.columns
        valid_sub = result[sub].dropna()
        assert (valid_sub >= 0.0).all()
        assert (valid_sub <= 1.0).all()
