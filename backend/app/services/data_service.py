"""
Data service — loads processed artefacts and caches them in memory.
Avoids reloading parquet/json on every request.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class DataService:
    _meei: pd.DataFrame | None = None
    _raw: pd.DataFrame | None = None
    _iop: dict | None = None
    _global_shap: dict | None = None
    _local_shap: list | None = None
    _local_shap_index: dict | None = None
    _eval_report: dict | None = None
    _priorities: dict | None = None

    def _load(self, path: Path, kind: str):
        if not path.exists():
            logger.warning("File not found: %s (%s). Run pipeline first.", path, kind)
            return None
        try:
            if path.suffix == ".parquet":
                return pd.read_parquet(path)
            elif path.suffix == ".json":
                with open(path) as f:
                    return json.load(f)
            elif path.suffix == ".csv":
                return pd.read_csv(path)
        except Exception as e:
            logger.error("Error loading %s: %s", path, e)
        return None

    @property
    def meei(self) -> pd.DataFrame | None:
        if self._meei is None:
            self._meei = self._load(settings.processed_dir / "meei_results.parquet", "meei")
        return self._meei

    @property
    def raw(self) -> pd.DataFrame | None:
        if self._raw is None:
            self._raw = self._load(settings.processed_dir / "districts_demo.parquet", "raw")
        return self._raw

    @property
    def iop(self) -> dict | None:
        if self._iop is None:
            self._iop = self._load(settings.processed_dir / "iop_results.json", "iop")
        return self._iop

    @property
    def global_shap(self) -> dict | None:
        if self._global_shap is None:
            self._global_shap = self._load(
                settings.models_dir / "explainability" / "global_shap.json", "shap_global"
            )
        return self._global_shap

    @property
    def local_shap(self) -> list | None:
        if self._local_shap is None:
            self._local_shap = self._load(
                settings.models_dir / "explainability" / "local_shap.json", "shap_local"
            )
        return self._local_shap

    @property
    def local_shap_index(self) -> dict | None:
        if self._local_shap_index is None:
            self._local_shap_index = self._load(
                settings.models_dir / "explainability" / "local_shap_index.json", "shap_index"
            )
        return self._local_shap_index

    @property
    def eval_report(self) -> dict | None:
        if self._eval_report is None:
            self._eval_report = self._load(
                settings.models_dir / "predictive" / "evaluation_report.json", "eval"
            )
        return self._eval_report

    @property
    def priorities(self) -> dict | None:
        if self._priorities is None:
            self._priorities = self._load(
                settings.processed_dir / "priority_districts.json", "priorities"
            )
        return self._priorities

    def reload(self):
        self._meei = None
        self._raw = None
        self._iop = None
        self._global_shap = None
        self._local_shap = None
        self._local_shap_index = None
        self._eval_report = None
        self._priorities = None

    def ready(self) -> dict:
        return {
            "meei": self.meei is not None,
            "raw": self.raw is not None,
            "iop": self.iop is not None,
            "shap_global": self.global_shap is not None,
            "shap_local": self.local_shap is not None,
            "eval_report": self.eval_report is not None,
            "priorities": self.priorities is not None,
        }


data_service = DataService()

