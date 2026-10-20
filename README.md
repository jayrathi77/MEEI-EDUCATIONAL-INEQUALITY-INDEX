<<<<<<< HEAD
# Multidimensional Educational Equality Index (MEEI) & Predictive Disadvantage Platform

An end-to-end, scientifically grounded data science platform implementing the research paper:  
**"Measuring and Predicting Educational Disadvantage: A Multidimensional Equality Index for India"**

> **IMPORTANT DISCLAIMER**:  
> In compliance with strict academic integrity guidelines, all current figures in demo mode are computed using **synthetically generated demonstration data** with realistic multivariate distributions, covariance structures, and realistic missingness. No fabricated data are presented as real government statistics. When official government microdata/district tables (NAS, UDISE+, NSS/PLFS) are placed in `data/raw/`, the exact same pipeline generates official research estimates.

> **📖 Complete Documentation**: For an in-depth technical reference, mathematical formulations, indicators dictionary, and architecture breakdown, see [PROJECT_DOCUMENTATION.md](file:///d:/data%20science%20final/educational-equality-ml/PROJECT_DOCUMENTATION.md).

---

## 1. System Architecture

```
educational-equality-ml/
├── PROJECT_DOCUMENTATION.md          # Comprehensive technical & econometric documentation
├── data/
│   ├── raw/                       # Place official NAS, UDISE+, NSS data here
│   ├── processed/                 # Generated parquet/JSON artifacts
│   │   ├── districts_demo.parquet # 785 districts across all 36 States and UTs
│   │   ├── meei_results.parquet   # Computed sub-indices and composite MEEI
│   │   ├── iop_results.json       # Ex-ante IOp Gini metrics & circumstance rankings
│   │   └── priority_districts.json# Priority rankings and resource drivers
│   └── synthetic_demo/            # Reproducible synthetic data generation suite
│       └── generate_synthetic_data.py
├── scripts/                       # Reproducible ML & Econometric Pipeline
│   ├── build_meei.py              # Two-stage PCA + Varimax rotation + KMO/Bartlett
│   ├── estimate_iop.py            # Ex-ante Inequality of Opportunity & Gini
│   ├── train_models.py            # State-grouped CV (Ridge, RF, GBDT, ExtraTrees)
│   ├── generate_explanations.py   # Global & Local SHAP explainability
│   ├── build_priority_list.py     # Disadvantage ranking via documented decision rule
│   └── run_pipeline.py            # Master pipeline runner
├── models/
│   ├── index/                     # PCA diagnostics & eigenvectors
│   ├── predictive/                # Serialized models (.pkl) & CV evaluation report
│   └── explainability/            # Global & per-district local SHAP values
├── backend/                       # Production FastAPI REST Backend
│   ├── app/
│   │   ├── api/routes/            # Endpoints: overview, districts, index, iop, models, shap, priorities
│   │   ├── core/config.py         # App configuration & environment settings
│   │   ├── services/data_service.py # In-memory caching & parquet query engine
│   │   └── main.py                # FastAPI app entry point with CORS & metadata
│   └── requirements.txt
├── frontend/                      # Modern React + TypeScript + Vite Dashboard
│   ├── src/
│   │   ├── pages/                 # Overview, District Explorer, IOp, Models, Priority
│   │   ├── components/            # Reusable UI cards, tables, score bars, badges
│   │   ├── services/api.ts        # Axios API client
│   │   └── index.css              # Dark-mode glassmorphic theme with Inter & JetBrains Mono
│   ├── package.json
│   └── vite.config.ts
├── tests/                         # Automated test suite (18/18 passing)
│   ├── test_meei.py               # Tests for PCA, KMO, Bartlett, sub-index bounds [0, 1]
│   ├── test_iop.py                # Tests for Gini coefficients and IOp calculation
│   ├── test_models.py             # Tests for state-grouped CV & metric reporting
│   └── test_api.py                # Full integration test of FastAPI REST endpoints
└── README.md
```

---

## 2. Research Methodology & Formulation

### Phase 1: Sub-Index & Composite Index (MEEI)
1. **Four Grouped Sub-Indices**:
   - **Academic Performance** ($I_{perf}$): Math & language scores across grades.
   - **Infrastructure** ($I_{infra}$): Electricity, drinking water, girls' toilets, permanent buildings, PTR (reversed).
   - **Equity** ($I_{equity}$): Gender and social group (SC/ST) performance gaps (inverted so higher = greater equality).
   - **Circumstances** ($I_{circ}$): Socioeconomic environment (parental literacy, urbanization, household income proxy).
2. **Kaiser-Meyer-Olkin (KMO) & Bartlett's Test of Sphericity** are computed prior to extraction to verify sampling adequacy.
3. **Extraction & Rotation**: Principal Component Analysis (eigenvalue $> 1$ Kaiser criterion) followed by **Varimax orthogonal rotation**. Sub-index scores are variance-weighted sums of retained rotated components.
4. **Stage 2 Composite (MEEI)**: A second-stage PCA on the four sub-indices yields the final composite MEEI, rescaled to $[0, 1]$ where higher values represent greater educational equality.

### Phase 2: Ex-Ante Inequality of Opportunity (IOp)
- **District-Level Approximation**: Ex-ante IOp calculates how much of total outcome dispersion is explained by circumstantial factors beyond a child's control:
  $$\text{Relative IOp} = \frac{G(\hat{y}_{types})}{G(y)}$$
  where $G(\cdot)$ denotes the Gini coefficient and $\hat{y}_{types}$ are conditional expectations estimated via Random Forest with out-of-fold predictions.
- **Conditional Permutation Importance**: Ranks circumstance variables by their marginal contribution to the inequality of opportunity.

### Phase 3: Spatial Grouped Predictive Modeling
- **Data Leakage Prevention**: Outcome-side target ($y$) strictly combines performance and equity sub-indices. Predictors ($X$) are restricted to infrastructure, institutional capacity, and circumstance indicators.
- **State-Grouped Cross-Validation**: Uses `GroupKFold` by state. Districts from the same state are held out together in validation folds to prevent geographic autocorrelation leakage.
- **Algorithms Evaluated**:
  - Ridge Regression (Interpretable linear baseline)
  - Random Forest Regressor
  - Gradient Boosting Regressor
  - Conditional Inference Forest (approximated via ExtraTrees in Python)
- **Reported Metrics**: RMSE, MAE, $R^2$, and Spearman rank correlation ($\rho$).

### Phase 4: Explainability (XAI)
- **SHAP (SHapley Additive exPlanations)** computes exact additive contributions of each infrastructure and circumstantial variable.
- Global feature importances identify systemic determinants across India; local SHAP breakdowns highlight specific bottlenecks for any selected district.

### Phase 5: Transparent Priority Formula
Districts are prioritized for policy interventions using a deterministic formula:
$$\text{Priority Score} = 0.5 \times (1 - \hat{y}_{\text{equality}}) + 0.3 \times (1 - I_{\text{infra}}) + 0.2 \times (1 - I_{\text{equity}})$$
Districts are ranked in descending order (Rank 1 = most disadvantaged / highest intervention priority).

---

## 3. Quick Start & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and npm

### Step 1: Run the Complete ML Pipeline
Run the master pipeline script which generates synthetic data, computes MEEI, estimates IOp, trains predictive models, produces SHAP values, and outputs the priority list:
```bash
python scripts/run_pipeline.py
```

### Step 2: Run the Automated Test Suite
Verify that all 18 unit and integration tests pass:
```bash
python -m pytest tests/ -v
```

### Step 3: Launch the FastAPI Backend
Start the high-performance REST API:
```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```
- Interactive API Swagger Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Step 4: Launch the React Frontend Dashboard
In a separate terminal:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## 4. Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health & data pipeline readiness |
| `/api/overview` | GET | National summary metrics, top/bottom districts |
| `/api/districts` | GET | Paginated list of districts with sub-indices & MEEI |
| `/api/districts/{id}` | GET | Specific district profile with radar metrics |
| `/api/index/summary` | GET | MEEI statistical distribution & sub-index summary |
| `/api/index/diagnostics` | GET | PCA eigenvalues, variance explained, loadings |
| `/api/iop/summary` | GET | Overall Gini, predicted Gini, relative IOp % |
| `/api/iop/circumstances` | GET | Ranked circumstances by permutation importance |
| `/api/models/comparison` | GET | Grouped-CV evaluation metrics (RMSE, MAE, $R^2$, $\rho$) |
| `/api/explainability/global` | GET | Global SHAP feature importances |
| `/api/explainability/district/{id}`| GET | Local SHAP drivers for a specific district |
| `/api/priorities` | GET | Filterable list of priority districts |
| `/api/priorities/export` | GET | Streamed CSV download of priority districts |
| `/api/methodology` | GET | Mathematical formulas & research definitions |
| `/api/data-sources` | GET | Official government data source documentation |

---

## 5. Verification & Test Status
- **Pipeline Execution**: Completed successfully in dependency order.
- **Test Suite**: 18 tests passing (`18 passed, 0 failed`).
- **Production Build**: Frontend Vite build completed cleanly (`dist/` generated).
=======
# MEEI-EDUCATIONAL-INEQUALITY-INDEX
>>>>>>> 06ec2a2f513b30d60e2e48e0175b77e3e1298c9c
