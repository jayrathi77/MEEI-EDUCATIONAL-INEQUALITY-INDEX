"""FastAPI main application entry point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import overview, districts, index, inequality, models, explainability, priorities

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "REST API for the Multidimensional Educational Equality Index (MEEI) platform — "
        "National Achievement Survey (NAS) & UDISE+ Harmonized Dataset."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router,       prefix="/api", tags=["Overview"])
app.include_router(districts.router,      prefix="/api", tags=["Districts"])
app.include_router(index.router,          prefix="/api", tags=["MEEI Index"])
app.include_router(inequality.router,     prefix="/api", tags=["Inequality of Opportunity"])
app.include_router(models.router,         prefix="/api", tags=["Predictive Models"])
app.include_router(explainability.router, prefix="/api", tags=["Explainability"])
app.include_router(priorities.router,     prefix="/api", tags=["Priority Districts"])


@app.get("/api/health", tags=["Health"])
def health():
    from app.services.data_service import data_service
    return {
        "status": "ok",
        "synthetic_mode": settings.synthetic_mode,
        "data_ready": data_service.ready(),
    }


@app.get("/api/methodology", tags=["Documentation"])
def methodology():
    return {
        "title": "MEEI Methodology",
        "index_construction": {
            "stage1": "PCA per group (Performance, Infrastructure, Equity, Circumstances) with eigenvalue>1 retention and Varimax rotation",
            "stage2": "Second PCA on four sub-indices to obtain MEEI",
            "rescaling": "Min-max [0,1]; higher = better equality",
        },
        "iop": {
            "method": "Ex-ante IOp via conditional expectation (Random Forest cross-val prediction)",
            "gini": "Standard Gini coefficient on outcome distribution",
            "level": "District-level approximation — NOT individual-level",
            "caveat": "Individual-level IOp requires household microdata (NSS/PLFS).",
        },
        "models": {
            "ridge": "Ridge Regression — interpretable linear baseline",
            "rf": "Random Forest",
            "gb": "Gradient Boosting",
            "cif": "Conditional Inference Forest — approximated by ExtraTreesRegressor (genuine CIF requires R partykit)",
        },
        "validation": "State-grouped k-fold cross-validation (GroupKFold). All districts from one state held out together.",
        "explainability": "SHAP TreeExplainer (tree models) or KernelExplainer (linear). Values describe prediction contributions, NOT causal effects.",
        "priority_rule": "Priority Score = 0.5×(1-pred_equality) + 0.3×(1-infra) + 0.2×(1-equity)",
    }


@app.get("/api/data-sources", tags=["Documentation"])
def data_sources():
    return {
        "sources": [
            {
                "name": "National Achievement Survey (NAS)",
                "publisher": "Ministry of Education, Government of India",
                "url": "https://nas.gov.in/",
                "variables": ["Math & Language achievement by class and district", "Gender/rural-urban/SC-ST breakdowns"],
                "status": "Manual download required — see README.md",
            },
            {
                "name": "UDISE+",
                "publisher": "Department of School Education & Literacy",
                "url": "https://udiseplus.gov.in/",
                "variables": ["School infrastructure", "Teacher availability", "Enrolment"],
                "status": "Manual download required — see README.md",
            },
            {
                "name": "NSS / PLFS (Household surveys)",
                "publisher": "Ministry of Statistics, Government of India",
                "url": "https://mospi.gov.in/",
                "variables": ["Parental education", "Occupation", "Social group", "Urban/rural"],
                "status": "Manual download required — district linkage depends on survey year",
            },
        ],
        "current_data": "NAS_UDISE_PLFS_HARMONIZED",
        "dataset_name": "National Educational Survey Dataset (NAS-UDISE+ Integrated)",
        "coverage": "All 36 States & Union Territories (785 Districts)",
    }
