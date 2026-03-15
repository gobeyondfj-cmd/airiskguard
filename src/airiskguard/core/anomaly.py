"""Anomaly detection — IsolationForest + KS drift detection."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest

from airiskguard.types import RiskLevel

logger = logging.getLogger(__name__)


class AnomalyDetector:

    def __init__(self, contamination: float = 0.1, drift_significance: float = 0.05) -> None:
        self._contamination = contamination
        self._drift_significance = drift_significance
        self._models: dict[str, IsolationForest] = {}
        self._baselines: dict[str, np.ndarray] = {}
        self._alerts: list[dict[str, Any]] = []

    def fit(self, model_id: str, data: np.ndarray) -> None:
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        clf = IsolationForest(contamination=self._contamination, random_state=42)
        clf.fit(data)
        self._models[model_id] = clf
        self._baselines[model_id] = data.copy()

    def predict(self, model_id: str, data: np.ndarray) -> dict[str, Any]:
        if model_id not in self._models:
            return {"anomaly": False, "scores": [], "risk_level": RiskLevel.LOW}

        if data.ndim == 1:
            data = data.reshape(-1, 1)

        clf = self._models[model_id]
        predictions = clf.predict(data)
        scores = clf.decision_function(data)

        anomaly_mask = predictions == -1
        anomaly_rate = float(anomaly_mask.mean())

        if anomaly_rate > 0.3:
            risk = RiskLevel.CRITICAL
        elif anomaly_rate > 0.15:
            risk = RiskLevel.HIGH
        elif anomaly_rate > 0.05:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW

        result = {
            "anomaly": bool(anomaly_mask.any()),
            "anomaly_rate": anomaly_rate,
            "scores": scores.tolist(),
            "anomaly_indices": np.where(anomaly_mask)[0].tolist(),
            "risk_level": risk,
        }

        if risk >= RiskLevel.HIGH:
            self._add_alert(model_id, "anomaly", result)

        return result

    def detect_drift(self, model_id: str, new_data: np.ndarray) -> dict[str, Any]:
        if model_id not in self._baselines:
            return {"drift_detected": False, "risk_level": RiskLevel.LOW}

        baseline = self._baselines[model_id]
        if baseline.ndim > 1:
            baseline = baseline.ravel()
        if new_data.ndim > 1:
            new_data = new_data.ravel()

        statistic, p_value = stats.ks_2samp(baseline, new_data)
        drift_detected = p_value < self._drift_significance

        if drift_detected and p_value < 0.001:
            risk = RiskLevel.CRITICAL
        elif drift_detected and p_value < 0.01:
            risk = RiskLevel.HIGH
        elif drift_detected:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW

        result = {
            "drift_detected": drift_detected,
            "ks_statistic": float(statistic),
            "p_value": float(p_value),
            "risk_level": risk,
        }

        if drift_detected:
            self._add_alert(model_id, "drift", result)

        return result

    def _add_alert(self, model_id: str, alert_type: str, details: dict[str, Any]) -> None:
        from airiskguard.utils.time_utils import utc_now_iso
        alert = {
            "model_id": model_id,
            "type": alert_type,
            "details": details,
            "timestamp": utc_now_iso(),
        }
        self._alerts.append(alert)
        logger.warning("Anomaly alert for %s: %s", model_id, alert_type)

    def get_alerts(self, model_id: str | None = None) -> list[dict[str, Any]]:
        if model_id:
            return [a for a in self._alerts if a["model_id"] == model_id]
        return list(self._alerts)

    def clear_alerts(self) -> None:
        self._alerts.clear()
