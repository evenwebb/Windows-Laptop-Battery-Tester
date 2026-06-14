"""
Discharge Rate Analyzer Module
Calculates real-time discharge rate and estimates time remaining.
"""


class DischargeAnalyzer:
    """Tracks discharge rate and estimates remaining runtime."""

    def __init__(self):
        self._start_pct = None
        self._start_seconds = 0
        self._last_pct = None
        self._last_seconds = 0
        self._rate_per_hour = 0.0
        self._short_term_rate = 0.0

    def update(self, battery_percent, elapsed_seconds):
        """Feed a new data point. Returns (rate_%/hr, estimated_minutes_remaining)."""
        if self._start_pct is None:
            self._start_pct = battery_percent
            self._start_seconds = elapsed_seconds

        # Overall rate (since start)
        pct_dropped = self._start_pct - battery_percent
        elapsed = max(elapsed_seconds - self._start_seconds, 1)
        if pct_dropped > 0:
            self._rate_per_hour = (pct_dropped / elapsed) * 3600

        # Short-term rate (last 2 data points)
        if self._last_pct is not None:
            pct_delta = self._last_pct - battery_percent
            time_delta = max(elapsed_seconds - self._last_seconds, 1)
            if pct_delta > 0:
                self._short_term_rate = (pct_delta / time_delta) * 3600

        self._last_pct = battery_percent
        self._last_seconds = elapsed_seconds

        rate = self._short_term_rate or self._rate_per_hour
        mins_remaining = (battery_percent / rate) * 60 if rate > 0 else 0
        return rate, mins_remaining

    def get_summary(self):
        """Return summary stats for the completed test."""
        return {
            "avg_rate_percent_per_hour": round(self._rate_per_hour, 2),
            "short_term_rate_percent_per_hour": round(self._short_term_rate, 2),
        }

    def reset(self):
        self.__init__()
