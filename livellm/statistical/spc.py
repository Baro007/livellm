"""
LiveLLM - Statistical Process Control (SPC)
Implements the Page-Hinkley test for subtle continuous capability degradation (Nerf)
and CUSUM for sudden step-change latency and throughput anomalies.
"""

from typing import List, Dict, Any, Tuple, Optional
import math


class PageHinkleyDetector:
    """
    Page-Hinkley sequential analysis test for detecting gradual mean degradation (drift/nerf).
    
    Equations:
      m_t = sum_{i=1}^t (e_i - x_bar_i + delta)
      M_t = min(m_i, i = 1 ... t)
      PH_t = m_t - M_t
      Alert if PH_t > lambda_threshold.
    """

    def __init__(self, delta: float = 0.01, threshold_lambda: float = 1.5, baseline_mean: Optional[float] = None):
        self.delta = delta
        self.threshold_lambda = threshold_lambda
        self.baseline_mean = baseline_mean
        self.reset()

    def reset(self):
        self.t = 0
        self.sum_errors = 0.0
        self.m_t = 0.0
        self.M_t = 0.0
        self.ph_series: List[float] = []
        self.alerts: List[int] = []

    def update(self, error_rate: float) -> Tuple[bool, float]:
        """
        Ingests a new error rate observation e_t (e.g., 1.0 - accuracy).
        Returns: (is_alert, ph_value)
        """
        self.t += 1
        self.sum_errors += error_rate
        x_bar_t = self.sum_errors / self.t

        # Cumulative deviation
        self.m_t += (error_rate - x_bar_t + self.delta)
        if self.t == 1:
            self.M_t = self.m_t
        else:
            self.M_t = min(self.M_t, self.m_t)

        ph_t = self.m_t - self.M_t
        self.ph_series.append(ph_t)

        is_alert = ph_t > self.threshold_lambda
        if is_alert:
            self.alerts.append(self.t)

        return is_alert, ph_t


class CusumDetector:
    """
    Cumulative Sum (CUSUM) detector for abrupt mean shifts in continuous signals
    such as TTFT latency spikes or sharp drops in TPS.
    """

    def __init__(self, target_mean: Optional[float] = None, slack_k: float = 1.0, threshold_h: float = 5.0):
        self.target_mean = target_mean
        self.slack_k = slack_k
        self.threshold_h = threshold_h
        self.reset()

    def reset(self):
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.history: List[float] = []
        self.alerts_high: List[int] = []
        self.alerts_low: List[int] = []
        self.count = 0
        self.running_sum = 0.0

    def update(self, value: float) -> Tuple[bool, str, float]:
        """
        Ingests a new metric value (e.g. latency in ms or TPS).
        Returns: (is_alert, direction ['high'|'low'|'normal'], max_cusum_stat)
        """
        self.count += 1
        self.running_sum += value
        mean = self.target_mean if self.target_mean is not None else (self.running_sum / self.count)

        # Upper CUSUM (detects upward shifts, e.g. latency spikes)
        self.s_pos = max(0.0, self.s_pos + (value - mean - self.slack_k))
        # Lower CUSUM (detects downward shifts, e.g. TPS collapse)
        self.s_neg = max(0.0, self.s_neg - (value - mean + self.slack_k))

        alert_high = self.s_pos > self.threshold_h
        alert_low = self.s_neg > self.threshold_h

        if alert_high:
            self.alerts_high.append(self.count)
            return True, "high", self.s_pos
        elif alert_low:
            self.alerts_low.append(self.count)
            return True, "low", self.s_neg

        return False, "normal", max(self.s_pos, self.s_neg)
