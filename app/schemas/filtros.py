from pydantic import BaseModel, Field
from typing import Optional, Dict

class ArtifactsInfo(BaseModel):
    doc_id: str
    doc_url: str

class DiagnosticsInfo(BaseModel):
    processing_time_ms: int
    model_version: str

class FiltrosCallbackPayload(BaseModel):
    """Payload recibido desde el servicio FILTROS."""
    task_id: str
    status: str
    outcome: Optional[str] = None
    artifacts: Optional[ArtifactsInfo] = None
    diagnostics: Optional[DiagnosticsInfo] = None
    error: Optional[str] = None
