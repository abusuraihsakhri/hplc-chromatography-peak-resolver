"""Regression checks for independent chromatogram processing and audit signatures."""
import math

import pytest

from hplc_resolver.peaks import parse_chromatogram, analyze_trace
from agents.base import AuditTrail


def synthetic():
    return [
        (i * 0.05, 2 + 28 * math.exp(-0.5 * ((i * 0.05 - 5) / 0.5) ** 2)
         + 20 * math.exp(-0.5 * ((i * 0.05 - 13) / 0.8) ** 2))
        for i in range(401)
    ]


def test_peak_detection_and_resolution():
    result = analyze_trace(synthetic(), min_prominence=0.05, dead_time=1)
    peaks = result["peaks"]
    assert len(peaks) == 2
    assert peaks[0]["retentionTime"] == pytest.approx(5, abs=0.05)
    assert peaks[1]["retentionTime"] == pytest.approx(13, abs=0.05)
    assert peaks[0]["retentionFactor"] == pytest.approx(4, abs=0.05)
    assert peaks[1]["resolutionFromPrevious"] > 2
    assert all(p["area"] > 0 for p in peaks)
    assert sum(p["areaPercent"] for p in peaks) == pytest.approx(100)


def test_csv_parse_and_validation():
    csv = "time,signal\n0,1\n1,3\n2,4\n3,3\n4,1\n"
    assert len(parse_chromatogram(csv)) == 5
    assert len(parse_chromatogram(csv.replace(",", "\t"))) == 5
    with pytest.raises(ValueError, match="increase"):
        parse_chromatogram("0,1\n1,2\n1,3\n3,2\n4,1")
    with pytest.raises(ValueError, match="Non-finite"):
        parse_chromatogram("0,1\n1,2\n2,nan\n3,2\n4,1")
    with pytest.raises(ValueError, match="non-increasing"):
        analyze_trace([(i, float("nan") if i == 3 else 1) for i in range(6)])
    with pytest.raises(ValueError, match="prominence"):
        analyze_trace(synthetic(), min_prominence=0)
    with pytest.raises(ValueError, match="positive"):
        analyze_trace(synthetic(), dead_time=-2)


def test_flat_trace_is_empty():
    assert analyze_trace([(i, 1) for i in range(9)])["peaks"] == []


def test_signed_audit_chain_rejects_tampering():
    trail = AuditTrail(secret_key="a" * 32)
    trail.log("tester", "worker", "checked", {"value": 4})
    trail.log("tester", "worker", "checked", {"value": 5})
    assert trail.verify_integrity()
    detached = trail.get_trail()
    detached[0]["actor"] = "attacker"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "attacker"
    assert not trail.verify_integrity()


def test_second_hash_edit_is_rejected():
    trail = AuditTrail(secret_key="b" * 32)
    trail.log("tester", "worker", "checked", {"value": 4})
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()
