"""
FastAPI REST API Server for Hplc Chromatography Peak Resolver.
"""
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from hplc_resolver.peaks import analyze_trace
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Hplc Chromatography Peak Resolver API",
    description="Enterprise Distributed Component Platform (AI Drug Discovery, Structural Biology & Wet-Lab Robotics)",
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
    return {"status": "HEALTHY", "service": "hplc-chromatography-peak-resolver", "domain": "AI Drug Discovery, Structural Biology & Wet-Lab Robotics", "standard": "wwPDB / IUPAC / OpenSMILES / ISAC Standards", "version": "3.0.0-ENTERPRISE"}


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
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
