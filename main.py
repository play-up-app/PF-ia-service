from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import des routes
from app.api.routes.planning import router as planning_router


# Création de l'app FastAPI
app = FastAPI(
    title="AI Planning Service API",
    description="API pour la génération automatique de plannings de tournois de volley-ball",
    version="1.0.0",
    docs_url="/docs"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À configurer selon l'environnement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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