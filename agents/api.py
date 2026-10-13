"""
FastAPI REST API Server for Hplc Chromatography Peak Resolver.
"""
import os
import hmac
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from hplc_resolver.peaks import analyze_trace
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Hplc Chromatography Peak Resolver API",
    description="HPLC trace peak calculations and legacy threshold-based task auditing",
    version="3.0.0-ENTERPRISE",
)


class PeakRequest(BaseModel):
    samples: List[Tuple[float, float]]
    min_prominence: float = 0.06
    dead_time: Optional[float] = None


@app.post("/api/peaks")
def api_peaks(req: PeakRequest):
    try:
        return analyze_trace(req.samples, req.min_prominence, req.dead_time)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "hplc-chromatography-peak-resolver", "domain": "Analytical Chemistry", "standard": "User-defined metric thresholds; not validated against a pharmacopeial monograph", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(x_admin_token: Optional[str] = Header(default=None)):
    """Audit metadata is accessible only with a separately configured admin token."""
    expected = os.getenv("API_ADMIN_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail="Admin audit access is not configured")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
