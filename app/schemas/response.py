from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.models.models import AITournamentPlanning

class StandardResponse(BaseModel):
    """Réponse standard de l'API"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PlanningResponse(StandardResponse):
    """Réponse avec données de planning"""
    data: Optional[AITournamentPlanning] = None

class StatusResponse(StandardResponse):
    """Réponse avec statut de planning"""
    data: Optional[Dict[str, str]] = None