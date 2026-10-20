# Multidimensional Educational Equality Index (MEEI) Platform
## Complete Project Documentation & Technical Reference Manual

---

## 1. Executive Summary & Project Purpose

The **Multidimensional Educational Equality Index (MEEI) Platform** is an end-to-end, scientifically grounded data science and machine learning platform designed to measure, diagnose, predict, and address district-level educational disparities across India.

### Core Problem
India's school education system exhibits substantial spatial, socioeconomic, and infrastructural inequality. Traditional educational metrics usually evaluate only raw academic test scores, ignoring:
1. **Multidimensional inputs** (school infrastructure, basic amenities, pupil-teacher ratios).
2. **Equity and disparity dimensions** (gender achievement gaps, rural-urban divisions, social category gaps).
3. **Circumstantial factors** beyond a student's control (parental literacy, parental occupation, urbanization, district development).

### The Solution: MEEI Framework
The MEEI framework synthesizes these components through:
- **Two-Stage Principal Component Analysis (PCA)** with statistical suitability verification (KMO & Bartlett tests) and Varimax orthogonal rotation to construct an objective, composite equality index bounded in $[0, 1]$.
- **Roemer's Framework for Inequality of Opportunity (IOp)** to calculate the Gini coefficient of conditional expectations and quantify what share of educational inequality is strictly attributable to predetermined circumstances.
- **Spatially-Grouped Machine Learning Regressors** (Ridge, Random Forest, Gradient Boosting, Extra Trees approximation of Conditional Inference Forests) validated using state-grouped cross-validation (`GroupKFold`) to avoid spatial autocorrelation data leakage.
- **Explainable AI (SHAP)** to compute systemic national drivers (global SHAP) and actionable local bottlenecks for each district (local SHAP).
- **A Transparent Resource Allocation Priority Formula** to directly translate econometric and ML findings into targeted policy interventions.

---

## 2. Project Scope & Geographical Scale

- **Total States and Union Territories**: **36** (All 28 Indian States + 8 Union Territories).
- **Total Districts Covered**: **785 official districts** representing 100% complete all-India coverage.
- **Data Mode**:
  - **Synthetic Demo Mode**: Fully calibrated synthetic data with multivariate covariance structures, regional development baselines, and realistic missingness.
  - **Production / Real Data Mode**: When official datasets (NAS, UDISE+, PLFS) are placed into `data/raw/`, the exact same pipeline generates official research estimates without code modifications.

---

## 3. Directory Structure & Architecture

```
educational-equality-ml/
├── PROJECT_DOCUMENTATION.md          # Complete project technical documentation (this file)
├── README.md                          # Quick start, setup instructions & verification
├── run_pipeline.py                    # Root script runner for the complete pipeline
│
├── data/
│   ├── raw/                           # Directory for official raw government datasets (NAS, UDISE+, NSS)
│   ├── interim/                       # Intermediate merged tabular formats
│   ├── reference/                     # Codebooks, indicator metadata, state mappings
│   ├── processed/                     # Pipeline output artifacts consumed by backend
│   │   ├── districts_demo.parquet     # Master indicators table for all 785 districts
│   │   ├── meei_results.parquet       # Sub-indices (Perf, Infra, Equity, Circ) & composite MEEI
│   │   ├── meei_results.csv           # Tabular CSV export of MEEI results
│   │   ├── iop_results.json           # Ex-ante IOp Gini metrics & circumstance rankings
│   │   ├── priority_districts.parquet # Priority score calculations and rank ordering
│   │   ├── priority_districts.csv     # Exportable CSV for educational administrators
│   │   └── priority_districts.json    # JSON artifact with drivers for API delivery
│   └── synthetic_demo/                # Synthetic data generator
│       ├── generate_synthetic_data.py # Generator for all 36 States/UTs and 785 districts
│       ├── synthetic_districts.csv    # CSV copy of generated demo data
│       └── synthetic_manifest.json    # Metadata manifest of generation run
│
├── scripts/                           # Reproducible ML & Econometric Pipeline
│   ├── build_meei.py                  # Two-stage PCA + Varimax rotation + KMO/Bartlett tests
│   ├── estimate_iop.py                # Ex-ante Inequality of Opportunity (IOp) calculation
│   ├── train_models.py                # State-grouped cross-validation of 4 ML models
│   ├── generate_explanations.py       # Global and local SHAP explainability generation
│   ├── build_priority_list.py         # Priority score calculator & decision rule execution
│   └── run_pipeline.py                # Master orchestrator executing steps in dependency order
│
├── models/
│   ├── index/                         # MEEI weights, PCA models, and diagnostics JSON
│   │   └── meei_diagnostics.json      # KMO, Bartlett p-values, explained variance ratios
│   ├── predictive/                    # Serialized machine learning models (.joblib / .pkl)
│   │   ├── best_model.joblib          # Selected best predictive model
│   │   ├── feature_metadata.json      # Feature list, scaling rules, target definitions
│   │   └── evaluation_report.json     # Grouped CV metrics (RMSE, MAE, R², Spearman rho)
│   └── explainability/                # SHAP explanation objects
│       ├── global_shap.json           # National feature importance rankings
│       ├── local_shap.json            # District-by-district SHAP feature contributions
│       └── local_shap_index.json      # Fast O(1) lookup index for district IDs
│
├── backend/                           # Production FastAPI REST API
│   ├── app/
│   │   ├── main.py                    # Application entry point, middleware, route registration
│   │   ├── core/
│   │   │   └── config.py              # Environment configuration, path resolution, settings
│   │   ├── services/
│   │   │   └── data_service.py        # In-memory cached query engine for parquet/json
│   │   └── api/
│   │       └── routes/                # Domain-specific route controllers
│   │           ├── overview.py        # National KPI summary, top/bottom rankings, state stats
│   │           ├── districts.py       # District pagination, detail view, radar indicators
│   │           ├── index.py           # MEEI index distributions & PCA diagnostics
│   │           ├── inequality.py      # IOp Gini metrics & circumstance importance
│   │           ├── models.py          # Model cross-validation comparison & metric report
│   │           ├── explainability.py  # Global & local SHAP explanations
│   │           └── priorities.py      # Prioritized district rankings & CSV streaming export
│   └── requirements.txt               # Backend dependencies (FastAPI, uvicorn, pandas, etc.)
│
├── frontend/                          # React + TypeScript + Vite Dashboard
│   ├── index.html                     # HTML root template with fonts and meta tags
│   ├── package.json                   # Frontend dependencies (React, Recharts, Lucide, Axios)
│   ├── vite.config.ts                 # Vite bundler configuration
│   └── src/
│       ├── App.tsx                    # React router provider
│       ├── main.tsx                   # React DOM root render
│       ├── index.css                  # Custom styling system, color tokens, dark glassmorphism
│       ├── layouts/
│       │   └── AppLayout.tsx          # Shell layout: sticky sidebar, top status, navigation
│       ├── types/
│       │   └── api.ts                 # TypeScript interfaces for all backend data contracts
│       ├── services/
│       │   └── api.ts                 # Axios API service client with automatic base URL
│       ├── hooks/
│       │   └── useApi.ts              # Custom asynchronous hook with formatted error handling
│       ├── components/
│       │   └── ui/
│       │       └── Common.tsx         # ScoreBar, Badges, LoadingState, ErrorState, KPI cards
│       └── pages/
│           ├── OverviewPage.tsx       # National overview KPI cards, charts, state rankings
│           ├── DistrictExplorerPage.tsx # Searchable, sortable catalog of all 785 districts
│           ├── DistrictProfilePage.tsx # Detailed district analysis: radar chart, SHAP waterfall
│           ├── DistrictPage.tsx       # Interactive single-district explorer
│           ├── InequalityPage.tsx     # IOp breakdown, circumstance drivers, Gini curves
│           ├── ModelsPage.tsx         # Model performance comparison (RMSE, MAE, R², Spearman)
│           ├── PriorityPage.tsx       # Priority intervention table with state filters & CSV export
│           └── MethodologyPage.tsx    # Technical documentation & data source citations
│
└── tests/                             # Automated Test Suite (Pytest)
    ├── test_meei.py                   # Tests PCA correctness, KMO/Bartlett, bounds [0, 1]
    ├── test_iop.py                    # Tests Gini calculation and Roemer IOp bounds
    ├── test_models.py                 # Tests GroupKFold validation, leakage absence, metrics
    └── test_api.py                    # Tests FastAPI HTTP endpoints
```

---

## 4. Key Indicators & Data Model

The platform monitors **23 distinct educational indicators** across 4 functional domains:

### Domain 1: Academic Performance Sub-Index ($I_{perf}$)
- `nas_math_cl3`: National Achievement Survey Math Score for Class 3.
- `nas_lang_cl3`: NAS Language Score for Class 3.
- `nas_math_cl5`: NAS Math Score for Class 5.
- `nas_lang_cl5`: NAS Language Score for Class 5.
- `nas_math_cl8`: NAS Math Score for Class 8.
- `nas_lang_cl8`: NAS Language Score for Class 8.

### Domain 2: Infrastructure Sub-Index ($I_{infra}$)
- `pct_schools_electricity`: Percentage of schools with functional electricity connection.
- `pct_schools_drinking_water`: Percentage of schools with functional drinking water.
- `pct_schools_toilets`: Percentage of schools with functional separate toilets.
- `pct_schools_computers`: Percentage of schools with functional computer facilities.
- `pct_schools_library`: Percentage of schools with book banks/libraries.
- `pct_schools_permanent_building`: Percentage of schools in permanent pucca structures.
- `pupil_teacher_ratio`: Pupil-Teacher Ratio (PTR; inverted in scoring).
- `pct_schools_medical_checkup`: Percentage of schools conducting annual health screenings.
- `pct_govt_schools`: Share of government-managed schools in the district.

### Domain 3: Equity & Disparities Sub-Index ($I_{equity}$)
- `gender_gap_math_cl5`: Male minus female average score difference (closer to 0 is better).
- `gender_gap_lang_cl5`: Male minus female language score difference.
- `rural_urban_gap_math`: Achievement differential between urban and rural schools.
- `sc_gap_math_cl5`: Achievement gap for Scheduled Caste (SC) students vs non-SC.
- `st_gap_math_cl5`: Achievement gap for Scheduled Tribe (ST) students vs non-ST.
*Note: Gaps are transformed such that higher index scores represent greater equality.*

### Domain 4: Circumstances Sub-Index ($I_{circ}$)
- `pct_literate_parents`: Percentage of students whose parents are literate.
- `pct_urban_hh`: Urbanization level (% of urban households in the district).
- `pct_sc_st_population`: Combined SC and ST population share in the district.
- `pct_professional_occupation`: Share of households in formal/professional occupations.
- `hdi_proxy`: Composite Human Development Index proxy score for the district.

---

## 5. Mathematical & Econometric Methodology

### 5.1 Two-Stage Principal Component Analysis (MEEI Construction)

```
[23 Raw Indicators] ──> Grouped into 4 Sets (Perf, Infra, Equity, Circ)
                                     │
                        Check KMO (> 0.50) & Bartlett's Test (p < 0.05)
                                     │
                        Stage 1 PCA per Group (Eigenvalue > 1.0)
                                     │
                        Varimax Orthogonal Factor Rotation
                                     │
                        Variance-Weighted Score per Domain [0, 1]
                                     │
                       4 Sub-Indices: I_perf, I_infra, I_equity, I_circ
                                     │
                        Stage 2 PCA across the 4 Sub-Indices
                                     │
                        Final Composite MEEI Score [0, 1]
```

1. **Standardization**: Indicators are centered and scaled: $z = \frac{x - \mu}{\sigma}$.
2. **Kaiser-Meyer-Olkin (KMO) Measure**: Assesses sampling adequacy:
   $$\text{KMO} = \frac{\sum_{i \neq j} r_{ij}^2}{\sum_{i \neq j} r_{ij}^2 + \sum_{i \neq j} q_{ij}^2}$$
3. **Bartlett's Test of Sphericity**: Validates that correlation matrix is not an identity matrix.
4. **Varimax Rotation**: Orthogonal rotation of factor loadings to maximize interpretability:
   $$R = \arg\max_R \sum_{k=1}^m \left[ \sum_{j=1}^p \Lambda_{jk}^4 - \frac{1}{p} \left(\sum_{j=1}^p \Lambda_{jk}^2\right)^2 \right]$$
5. **Stage 2 Composite (MEEI)**: Second PCA on the 4 sub-indices yields the final composite MEEI. Values are min-max normalized to $[0, 1]$ where 1.0 represents the highest equality and 0.0 represents the most severe disadvantage.

### 5.2 Ex-Ante Inequality of Opportunity (IOp)
Based on John Roemer's economic theory of equal opportunity:
- Outcomes $y$ are partitioned into **Effort** (within-district individual factors) and **Circumstance** (predetermined background characteristics $C$).
- Conditional expectations are predicted using machine learning: $\hat{y} = \mathbb{E}[y \mid C]$.
- **Absolute IOp** is the Gini index of the conditional distribution:
  $$\text{Absolute IOp} = G(\hat{y})$$
- **Relative IOp** represents the percentage of total outcome inequality directly attributable to circumstances:
  $$\text{Relative IOp} = \frac{G(\hat{y})}{G(y)} \times 100\%$$
- **Circumstance Importance**: Permutation importance across out-of-fold folds isolates the marginal contribution of each circumstance variable.

---

## 6. Machine Learning Pipeline & Spatial Cross-Validation

### 6.1 Data Leakage Prevention
To ensure strict econometric validity:
- **Target ($y$)**: Outcome-side equality (average of Performance and Equity sub-indices).
- **Features ($X$)**: Restricted strictly to input-side infrastructure and circumstance indicators.
- **No Self-Correlation Leakage**: Target indicators are never present in the predictor matrix.

### 6.2 Spatial State-Grouped Cross-Validation (`GroupKFold`)
Neighboring districts often share geographical, budgetary, and administrative conditions. Standard random $k$-fold cross-validation results in severe spatial data leakage.
- We utilize **5-fold `GroupKFold` grouped by `state_name`**.
- All districts from the same state are held out together in validation folds.
- The model must generalize to unseen states and regions.

### 6.3 Models Evaluated & Metric Standards
1. **Ridge Regression**: Regularized $L_2$ linear model providing an interpretable baseline.
2. **Random Forest Regressor**: Non-linear ensemble of decision trees capturing interactions.
3. **Gradient Boosting Regressor**: Sequentially optimized boosted trees.
4. **Conditional Inference Forest (CIF Approximation)**: Implemented via ExtraTrees with permutation splitting to handle variable selection bias without overfitting correlated predictors.

**Performance Metrics Tracked**:
- **RMSE** (Root Mean Squared Error)
- **MAE** (Mean Absolute Error)
- **$R^2$** (Coefficient of Determination)
- **Spearman Rank Correlation ($\rho$)** (Monotonic ordering accuracy)

---

## 7. Explainable AI (SHAP)

To avoid black-box decision making in public policy:
- **Global SHAP**: Aggregates the mean absolute Shapley values ($E[|\phi_j|]$) across all 785 districts to establish the nationwide hierarchy of disadvantage drivers.
- **Local SHAP Waterfall**: For any selected district, decomposes its predicted equality score into exact positive and negative feature contributions:
  $$\hat{y}_i = \mathbb{E}[y] + \sum_{j=1}^{P} \phi_{ij}$$
  This reveals precisely why a specific district scored poorly (e.g. lack of electricity, severe pupil-teacher ratio, or low parental literacy).

---

## 8. Policy Intervention Priority Rule

Districts are systematically ranked for educational resource allocation using a multi-criteria decision formula:

$$\text{Priority Score} = 0.5 \times (1 - \hat{y}_{\text{equality}}) + 0.3 \times (1 - I_{\text{infra}}) + 0.2 \times (1 - I_{\text{equity}})$$

### Rule Components:
- $0.5 \times (1 - \hat{y}_{\text{equality}})$: Targets districts with low predicted learning equality.
- $0.3 \times (1 - I_{\text{infra}})$: Directly incorporates infrastructural deficits.
- $0.2 \times (1 - I_{\text{equity}})$: Accounts for severe demographic and gender achievement gaps.

**Ranking**:
- **Rank 1**: Highest priority score (most disadvantaged; requires immediate intervention).
- **Rank 785**: Lowest priority score (best performing; self-sustaining).
- Direct export available as CSV via the backend `/api/priorities/export` endpoint.

---

## 9. Backend API Reference Catalog

The backend runs on **FastAPI** on `http://localhost:8000`. Full interactive Swagger documentation is available at `http://localhost:8000/docs`.

| Endpoint | Method | Query Parameters | Description |
|---|---|---|---|
| `/api/health` | GET | None | System status, synthetic data mode flag, pipeline readiness check. |
| `/api/overview` | GET | None | National summary metrics, total districts (785), total states (36), mean/median MEEI, top 5 and bottom 5 districts, state averages. |
| `/api/districts` | GET | `state`, `page`, `page_size` (up to 2000) | Paginated list of all 785 districts with composite MEEI, ranks, and 4 sub-indices. |
| `/api/districts/{id}` | GET | `id` (e.g. `D091`) | Detailed district profile: raw indicators, sub-indices, state and national median comparisons. |
| `/api/index/summary` | GET | None | Statistical summary of composite MEEI distribution. |
| `/api/index/diagnostics` | GET | None | PCA variance explained ratios, factor loadings, KMO, Bartlett tests. |
| `/api/iop/summary` | GET | None | Ex-ante IOp Gini coefficient, predicted Gini, relative IOp percentage. |
| `/api/iop/circumstances` | GET | None | Circumstance variables ranked by permutation importance. |
| `/api/models/comparison` | GET | None | Grouped-CV evaluation metrics for Ridge, RF, GBDT, CIF. |
| `/api/models/validation` | GET | None | Fold-by-fold validation splits, test states, and features used. |
| `/api/explainability/global` | GET | None | Global SHAP feature importance rankings. |
| `/api/explainability/district/{id}`| GET | `id` | Local SHAP values and top positive/negative drivers for a district. |
| `/api/priorities` | GET | `state`, `page`, `page_size` (up to 2000) | Priority-ranked districts with key drivers and priority scores. |
| `/api/priorities/export` | GET | `state` | Generates streaming CSV download of priority districts. |
| `/api/methodology` | GET | None | JSON summary of mathematical formulas and pipeline rules. |
| `/api/data-sources` | GET | None | Citations and URLs for NAS, UDISE+, and NSS/PLFS surveys. |

---

## 10. Frontend Application Guide

The frontend is a single-page application built with **React 18**, **TypeScript**, and **Vite** running on `http://localhost:5173`.

### Visual Design System
- Modern dark-mode palette (`#0f172a` canvas, `#1e293b` surfaces, `#334155` borders).
- Typography powered by Google Fonts: **Inter** for clean readability, **JetBrains Mono** for numbers and metrics.
- Interactive visualizations built using **Recharts** (Radar charts, Bar charts, Reference lines).

### Key Pages
1. **National Overview (`/`)**: High-level KPI summary cards, national distribution histogram, state-by-state average MEEI bar chart, top 5 best performing and bottom 5 priority districts.
2. **District Explorer (`/districts`)**: Interactive catalog of all 785 districts. Filter by state, search by district name or ID, sort by MEEI score, rank, or sub-indices.
3. **District Detail (`/district/:id`)**: Comprehensive multi-tab profile for an individual district. Contains a 4-dimensional radar chart, indicator breakdown against state/national medians, and a local SHAP waterfall chart of key bottleneck factors.
4. **Drivers & Inequality of Opportunity (`/inequality`)**: Explores Roemer's IOp metrics, the share of inequality dictated by circumstances, and circumstance variable rankings.
5. **Model Comparison (`/models`)**: Transparent machine learning evaluation comparing Ridge, Random Forest, GBDT, and CIF across spatially grouped cross-validation folds.
6. **Priority Districts (`/priorities`)**: Policy-focused action table ranking districts by intervention urgency with one-click CSV export for planners.
7. **Methodology & Data Sources (`/methodology`)**: Complete citations, documentation, and mathematical formulas for auditability.

---

## 11. How to Run the Platform

### Prerequisites
- Python 3.10+ (tested through Python 3.14)
- Node.js 18+ and npm

### 1. Execute the ML Pipeline
To generate data and compute all econometric/ML artifacts for all 785 districts:
```powershell
python scripts/run_pipeline.py
```

### 2. Run the Backend API Server
```powershell
python -m uvicorn backend.app.main:app --port 8000 --reload
```
- API is accessible at: `http://localhost:8000`
- Swagger UI docs: `http://localhost:8000/docs`

### 3. Run the Frontend Development Server
```powershell
cd frontend
npm run dev
```
- Web dashboard is accessible at: `http://localhost:5173`

### 4. Run Automated Test Suite
```powershell
python -m pytest tests/ -v
```

---

## 12. Transitioning from Synthetic Demo to Real Data

To replace synthetic demo data with actual Indian government statistics:
1. Obtain official district-level data files:
   - **NAS (National Achievement Survey)**: `https://nas.gov.in/`
   - **UDISE+**: `https://udiseplus.gov.in/`
   - **NSS / PLFS**: `https://mospi.gov.in/`
2. Place cleaned CSV files into `data/raw/` matching the column schemas documented in Section 4.
3. In `backend/app/core/config.py`, toggle `SYNTHETIC_MODE = False`.
4. Re-run `python scripts/run_pipeline.py`.
The entire pipeline, API, and frontend dashboard will immediately reflect the authentic empirical findings.
