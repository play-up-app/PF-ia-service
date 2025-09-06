from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import des routes
from app.api.routes.planning import router as planning_router
from app.core.security import configure_security
from app.core.rate_limiter import configure_rate_limiter


# Création de l'app FastAPI
app = FastAPI(
    title="AI Planning Service API",
    description="API pour la génération automatique de plannings de tournois de volley-ball",
    version="1.0.0",
    docs_url="/docs"
)

# Configuration de sécurité complète (CORS + Headers de sécurité)
configure_security(app)

# Configuration du rate limiter
configure_rate_limiter(app)

# Inclusion des routes avec préfixes
app.include_router(planning_router)

# Route racine
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "success": True,
        "message": "AI Planning Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }