"""Tests for anomaly detector."""

import numpy as np
import pytest

from airiskguard.core.anomaly import AnomalyDetector
from airiskguard.types import RiskLevel


@pytest.fixture
def detector():
    return AnomalyDetector(contamination=0.1, drift_significance=0.05)


def test_fit_and_predict(detector):
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, 100)
    detector.fit("m1", normal_data)

    result = detector.predict("m1", np.array([0.5, -0.3, 0.1]))
    assert "anomaly" in result
    assert "scores" in result
    assert result["risk_level"] in list(RiskLevel)


def test_predict_anomalies(detector):
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, 200)
    detector.fit("m1", normal_data)

    # Extreme outliers
    outliers = np.array([50.0, -50.0, 100.0])
    result = detector.predict("m1", outliers)
    assert result["anomaly"] is True


def test_predict_no_model(detector):
    result = detector.predict("nonexistent", np.array([1.0, 2.0]))
    assert result["anomaly"] is False
    assert result["risk_level"] == RiskLevel.LOW


def test_drift_detection(detector):
    np.random.seed(42)
    baseline = np.random.normal(0, 1, 200)
    detector.fit("m1", baseline)

    # Same distribution — no drift
    same_dist = np.random.normal(0, 1, 200)
    result = detector.detect_drift("m1", same_dist)
    assert result["drift_detected"] == False

    # Different distribution — drift
    shifted = np.random.normal(5, 1, 200)
    result = detector.detect_drift("m1", shifted)
    assert result["drift_detected"] == True


def test_drift_no_baseline(detector):
    result = detector.detect_drift("nonexistent", np.array([1.0, 2.0]))
    assert result["drift_detected"] is False


def test_alerts(detector):
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, 200)
    detector.fit("m1", normal_data)

    outliers = np.array([50.0] * 50)
    detector.predict("m1", outliers)

    alerts = detector.get_alerts("m1")
    assert len(alerts) > 0

    detector.clear_alerts()
    assert len(detector.get_alerts()) == 0
