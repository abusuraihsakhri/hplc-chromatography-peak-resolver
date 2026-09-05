"""
Automated Pytest Test Suite for Hplc Chromatography Peak Resolver.
Domain: AI Drug Discovery, Structural Biology & Wet-Lab Robotics
Standard: wwPDB / IUPAC / OpenSMILES / ISAC Standards
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variable for audit trail before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-secret-key-for-pytest-min-32-chars-long")

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_nan_inf_rejection():
    """NaN and Inf metric values must be rejected by validation."""
    import math
    with pytest.raises(ValueError, match="NaN|Inf|finite"):
        SystemTaskPayload(task_id="T-NAN", target_identifier="K1", primary_metric=math.nan)
    with pytest.raises(ValueError, match="NaN|Inf|finite"):
        SystemTaskPayload(task_id="T-INF", target_identifier="K1", primary_metric=math.inf)


def test_path_traversal_protection():
    """CLI batch should reject paths that resolve outside the working directory."""
    from cli import _safe_resolve_path
    with pytest.raises(ValueError, match="traversal"):
        _safe_resolve_path("../../../etc/passwd")
    with pytest.raises(ValueError, match="traversal"):
        _safe_resolve_path("/etc/passwd")


def test_audit_key_required():
    """AuditTrail must reject empty/short keys when no env var is set."""
    from agents.base import AuditTrail, SecurityException
    # Temporarily clear the env var to test constructor validation
    original = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with pytest.raises(SecurityException):
            AuditTrail()
        with pytest.raises(SecurityException):
            AuditTrail(secret_key="")
        with pytest.raises(SecurityException):
            AuditTrail(secret_key="short")
        # Verify a valid key works
        trail = AuditTrail(secret_key="a" * 32)
        assert len(trail.logs) == 0
    finally:
        if original is not None:
            os.environ["AUDIT_SECRET_KEY"] = original
