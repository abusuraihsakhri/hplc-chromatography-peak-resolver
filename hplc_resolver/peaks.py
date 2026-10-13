"""Dependency-free HPLC trace peak detection and approximate integration.

Designed for exploratory peak screening. Not EMG/Gaussian deconvolution,
spectral purity analysis, or validated pharmacopeial suitability testing.
"""
from __future__ import annotations

import csv
import math
import re
from typing import Iterable, List, Optional, Sequence, Tuple

MAX_POINTS = 100_000


def parse_chromatogram(text: str) -> List[Tuple[float, float]]:
    """Parse time/signal CSV, TSV, or semicolon-separated data.

    The first two columns are used unless recognized header names identify
    other time and signal columns. Retention time must increase strictly.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("CSV input is empty.")
    text = text.lstrip("\ufeff")
    first = text.splitlines()[0]
    delim = max((",", "\t", ";"), key=lambda separator: first.count(separator))
    rows = [row for row in csv.reader(text.splitlines(), delimiter=delim)
            if any(cell.strip() for cell in row)]
    if len(rows) < 5:
        raise ValueError("At least five numeric samples are required.")
    if len(rows) > MAX_POINTS + 1:
        raise ValueError("CSV exceeds the 100,000-point limit.")

    def is_number(value: str) -> bool:
        try:
            return bool(value.strip()) and math.isfinite(float(value))
        except (ValueError, TypeError):
            return False

    has_header = len(rows[0]) < 2 or not (is_number(rows[0][0]) and is_number(rows[0][1]))
    header = [s.lower().strip() for s in rows.pop(0)] if has_header else []

    def index_for(pattern: str, default: int) -> int:
        return next((i for i, name in enumerate(header) if re.match(pattern, name)), default)

    time_index = index_for(r"^(time|retention.?time|rt|minutes|min)(\b|_)", 0)
    signal_index = index_for(r"^(signal|response|intensity|absorbance|area|uv|mau)(\b|_)",
                             1 if time_index == 0 else 0)
    if time_index == signal_index:
        raise ValueError("Time and signal columns must be distinct.")

    points = []
    for i, row in enumerate(rows, 1):
        try:
            t, y = float(row[time_index]), float(row[signal_index])
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid numeric data in row {i}.") from exc
        if not (math.isfinite(t) and math.isfinite(y)):
            raise ValueError(f"Non-finite numeric data in row {i}.")
        if points and t <= points[-1][0]:
            raise ValueError(f"Retention times must increase strictly (row {i}).")
        points.append((t, y))
    if len(points) < 5:
        raise ValueError("At least five numeric samples are required.")
    return points


def analyze_trace(
    points: Sequence[Tuple[float, float]],
    min_prominence: float = 0.06,
    dead_time: Optional[float] = None,
) -> dict:
    """Find local maxima and integrate individual valley-bounded peaks.

    Adjacent resolution uses Rs = 1.18 * (tR2 - tR1) / (FWHM1 + FWHM2).
    Areas are positive trapezoidal integrals above a local linear baseline.
    """
    if not math.isfinite(min_prominence) or not 0 < min_prominence < 1:
        raise ValueError("Minimum prominence must be between 0 and 1.")
    if dead_time is not None and (not math.isfinite(dead_time) or dead_time <= 0):
        raise ValueError("Dead time must be positive.")
    if not 5 <= len(points) <= MAX_POINTS:
        raise ValueError("Provide 5 to 100,000 samples.")

    values: List[Tuple[float, float]] = []
    for i, pair in enumerate(points):
        try:
            t, y = float(pair[0]), float(pair[1])
        except (TypeError, IndexError, ValueError) as exc:
            raise ValueError(f"Invalid sample {i+1}.") from exc
        if not (math.isfinite(t) and math.isfinite(y)) or (values and t <= values[-1][0]):
            raise ValueError(f"Non-finite value or non-increasing time at sample {i+1}.")
        values.append((t, y))

    n = len(values)
    y = [row[1] for row in values]
    smoothed = [y[i] if i in (0, n - 1)
                else (y[i-1] + 2*y[i] + y[i+1]) / 4 for i in range(n)]
    lo, hi = min(smoothed), max(smoothed)
    if hi <= lo:
        return {"peaks": [], "points": n, "minSignal": min(y), "maxSignal": max(y)}
    left_min: List[float] = []
    right_min: List[float] = [0.0] * n
    floor = math.inf
    for value in smoothed:
        floor = min(floor, value)
        left_min.append(floor)
    floor = math.inf
    for i in range(n-1, -1, -1):
        floor = min(floor, smoothed[i])
        right_min[i] = floor

    maxima = [
        i for i in range(1, n-1)
        if smoothed[i] > smoothed[i-1] and smoothed[i] >= smoothed[i+1]
        and smoothed[i] - max(left_min[i], right_min[i]) >= min_prominence * (hi-lo)
    ]
    valleys = [
        min(range(a, b), key=lambda i: smoothed[i])
        for a, b in zip(maxima, maxima[1:])
    ]

    def half_crossing(center: int, edge: int, half: float, direction: int) -> Optional[float]:
        i = center
        while i != edge:
            j = i + direction
            if smoothed[j] <= half:
                dy = smoothed[j] - smoothed[i]
                ratio = 0 if dy == 0 else (half - smoothed[i]) / dy
                return values[i][0] + ratio * (values[j][0] - values[i][0])
            i = j
        return None

    peaks = []
    for ordinal, peak_index in enumerate(maxima):
        left = 0 if ordinal == 0 else valleys[ordinal - 1]
        right = n - 1 if ordinal == len(maxima) - 1 else valleys[ordinal]
        baseline = max(smoothed[left], smoothed[right])
        height = max(0, smoothed[peak_index] - baseline)
        half = baseline + height / 2
        half_left = half_crossing(peak_index, left, half, -1) if height else None
        half_right = half_crossing(peak_index, right, half, 1) if height else None
        area = 0.0
        for j in range(left, right):
            b1 = y[left] + (y[right] - y[left]) * (
                values[j][0] - values[left][0]) / (values[right][0] - values[left][0])
            b2 = y[left] + (y[right] - y[left]) * (
                values[j+1][0] - values[left][0]) / (values[right][0] - values[left][0])
            area += (values[j+1][0] - values[j][0]) * (
                max(0, y[j] - b1) + max(0, y[j+1] - b2)) / 2
        rt = values[peak_index][0]
        peaks.append({
            "index": ordinal + 1,
            "retentionTime": rt,
            "height": height,
            "area": area,
            "areaPercent": 0.0,
            "fwhm": None if half_left is None or half_right is None else half_right - half_left,
            "resolutionFromPrevious": None,
            "retentionFactor": None if dead_time is None else (rt - dead_time) / dead_time,
            "startTime": values[left][0],
            "endTime": values[right][0],
        })
    area_total = sum(p["area"] for p in peaks)
    for i, peak in enumerate(peaks):
        peak["areaPercent"] = 100 * peak["area"] / area_total if area_total > 0 else 0
        if i and peak["fwhm"] is not None and peaks[i-1]["fwhm"] is not None:
            denom = peak["fwhm"] + peaks[i-1]["fwhm"]
            if denom > 0:
                peak["resolutionFromPrevious"] = 1.18 * (
                    peak["retentionTime"] - peaks[i-1]["retentionTime"]) / denom
    return {"peaks": peaks, "points": n, "minSignal": min(y), "maxSignal": max(y)}
