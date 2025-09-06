from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from app.core.config import settings

# Configuration du rate limiter
limiter = Limiter(key_func=get_remote_address)

def get_rate_limit_config():
    """
    Configuration des limites de taux selon l'environnement
    """
    if settings.ENVIRONMENT == "production":
        return {
            "default": "100/minute",  # 100 requêtes par minute par défaut
            "strict": "10/minute",     # 10 requêtes par minute pour les opérations sensibles
            "generous": "500/hour",    # 500 requêtes par heure pour les opérations légères
        }
    else:
        # En développement, limites plus permissives
        return {
            "default": "1000/minute",  # 1000 requêtes par minute par défaut
            "strict": "100/minute",    # 100 requêtes par minute pour les opérations sensibles
            "generous": "5000/hour",   # 5000 requêtes par heure pour les opérations légères
        }

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Gestionnaire personnalisé pour les dépassements de limite de taux
    """
    return Response(
        content={
            "success": False,
            "message": "Limite de taux dépassée. Veuillez réessayer plus tard.",
            "error": "RATE_LIMIT_EXCEEDED",
            "retry_after": exc.retry_after,
            "limit": exc.limit,
            "remaining": exc.remaining,
        },
        status_code=429,
        media_type="application/json"
    )

def configure_rate_limiter(app):
    """
    Configure le rate limiter pour l'application FastAPI
    """
    # Configuration du rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
