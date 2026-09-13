"""
LiveLLM - Tests for Statistical Process Control (Page-Hinkley & CUSUM)
"""

import pytest
from livellm.statistical.spc import PageHinkleyDetector, CusumDetector


def test_page_hinkley_stable_no_alert():
    ph = PageHinkleyDetector(delta=0.05, threshold_lambda=8.0)
    # Stable 5% error rate (high capability)
    for _ in range(30):
        is_alert, score = ph.update(0.05)
        assert is_alert is False


def test_page_hinkley_degradation_triggers_alert():
    ph = PageHinkleyDetector(delta=0.01, threshold_lambda=1.5)
    # Baseline: 20 days with 5% error rate
    for _ in range(20):
        ph.update(0.05)

    # Simulated Nerf: error rate leaps to 35%
    alert_triggered = False
    for day in range(15):
        is_alert, score = ph.update(0.35)
        if is_alert:
            alert_triggered = True
            break

    assert alert_triggered is True, "Page-Hinkley must detect sustained capability erosion"


def test_cusum_latency_spike():
    # Detect sharp spikes in TTFT (e.g. KV cache thrashing)
    cusum = CusumDetector(target_mean=250.0, slack_k=20.0, threshold_h=100.0)
    # Normal latency 250ms
    for _ in range(10):
        is_alert, direction, _ = cusum.update(250.0)
        assert is_alert is False

    # Massive 1200ms spike
    is_alert, direction, stat = cusum.update(1200.0)
    assert is_alert is True
    assert direction == "high"
