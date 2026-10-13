"""
FastAPI REST API Server for HPLC-Resolver: Chromatographic Peak Deconvolution & Purity Agent.
"""
from typing import Dict, Any, List, Optional, Tuple
from .models import FrontierPayload
from .agents import HPLCCoordinator
from .peaks import analyze_trace

coordinator = HPLCCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel

        app = FastAPI(
            title="HPLC-Resolver: Chromatographic Peak Deconvolution & Purity Agent",
            description="Fits exponentially modified Gaussian (EMG) functions, calculating retention factors (k'), peak asymmetry (As), and resolution (Rs).",
            version="2.0.0-FRONTIER",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = 28.5
            secondary_metric: float = 14.2
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = {}

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
            return {"status": "HEALTHY", "system": "hplc-chromatography-peak-resolver", "domain": "Analytical Chemistry", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            return coordinator.process(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
