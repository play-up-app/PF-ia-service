from pydantic import BaseModel, Field

class GeneratePlanningRequest(BaseModel):
    """Requête pour générer un planning"""
    tournament_id: str = Field(..., description="ID du tournoi (UUID)")

