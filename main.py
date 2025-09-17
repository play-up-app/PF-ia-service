import os
import uvicorn
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

# Configuration du port pour le déploiement
PORT = int(os.getenv("PORT", 8003))

# Route racine
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "success": True,
        "message": "AI Planning Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "port": PORT
    }


# Configuration du serveur pour le déploiement
if __name__ == "__main__":
    # Configuration du host selon l'environnement
    environment = os.getenv("ENVIRONMENT", "development")
    host = "0.0.0.0" if environment == "production" else "127.0.0.1"
    
    # Configuration de uvicorn
    config = {
        "host": host,
        "port": PORT,
        "log_level": "info" if environment == "production" else "debug",
        "access_log": True,
    }
    
    # En développement, ajouter le reload
    if environment == "development":
        config["reload"] = True
    
    print(f"🚀 Démarrage de l'AI Tournament Service")
    print(f"   - Environnement: {environment}")
    print(f"   - Host: {host}")
    print(f"   - Port: {PORT}")
    print(f"   - Documentation: http://{host}:{PORT}/docs")
    
    # Démarrage du serveur
    uvicorn.run("main:app", **config)