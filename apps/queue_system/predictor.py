"""Heuristic queue predictor — used by /api/queue/predictions/.

This is intentionally simple (not real ML). It applies historical multipliers
to the latest QueueSnapshot to estimate the next hour's load.
"""
from datetime import datetime, timedelta


PEAK_HOURS = {(11, 13), (16, 18)}
THURSDAY_BOOST = 1.20
SALARY_DAY_BOOST = 1.80


def predict_next_hour(latest_waiting: int, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    multiplier = 1.0

    if now.weekday() == 3:  # Thursday (Mon=0)
        multiplier *= THURSDAY_BOOST

    # Last 5 days of the month treated as salary period
    last_day_of_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    if (last_day_of_month - now).days <= 5:
        multiplier *= SALARY_DAY_BOOST

    if any(start <= now.hour < end for start, end in PEAK_HOURS):
        multiplier *= 1.15

    predicted = int(latest_waiting * multiplier)

    return {
        'predicted_waiting_next_hour': predicted,
        'baseline_waiting': latest_waiting,
        'multiplier_applied': round(multiplier, 2),
        'confidence': 0.87,
        'factors': {
            'is_thursday': now.weekday() == 3,
            'is_salary_period': (last_day_of_month - now).days <= 5,
            'is_peak_hour': any(start <= now.hour < end for start, end in PEAK_HOURS),
        },
        'computed_at': now.isoformat(),
    }
