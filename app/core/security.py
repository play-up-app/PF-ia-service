from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI
import os


def get_cors_config() -> dict:
    """
    Configuration CORS sécurisée pour l'API
    Couvre les principales vulnérabilités OWASP Top 10
    """
    # Récupération des origines autorisées depuis les variables d'environnement
    cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:3000")
    
    # Support de plusieurs origines séparées par des virgules
    allowed_origins = [origin.strip() for origin in cors_origin.split(",")]
    
    # En développement, ajouter localhost par défaut
    if "http://localhost:3000" not in allowed_origins and os.getenv("ENVIRONMENT") == "development":
        allowed_origins.append("http://localhost:3000")
    
    return {
        "allow_origins": allowed_origins,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization", 
            "X-Requested-With",
            "Accept",
            "Origin",
            "X-API-Key"
        ],
        "expose_headers": [
            "Content-Range", 
            "X-Content-Range",
            "X-Total-Count"
        ],
        "allow_credentials": True,
        "max_age": 86400,  # 24 heures
    }


def get_security_headers() -> dict:
    """
    Configuration des headers de sécurité
    Protection contre les principales vulnérabilités OWASP Top 10
    """
    return {
        # Protection XSS - Content Security Policy
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Cache DNS sécurisé
        "X-DNS-Prefetch-Control": "off",
        
        # Masquer le header X-Powered-By
        "X-Powered-By": None,
        
        # Protection contre le MIME-type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Politique de sécurité du contenu (CSP)
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        
        # Strict Transport Security (HSTS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        
        # Permissions Policy
        "Permissions-Policy": (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        ),
    }


def get_trusted_hosts() -> List[str]:
    """
    Configuration des hôtes de confiance
    """
    trusted_hosts_str = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # En production, utiliser les hôtes configurés
    if environment == "production":
        return [host.strip() for host in trusted_hosts_str.split(",") if host.strip()]
    
    # En développement, autoriser localhost et les hôtes configurés
    default_hosts = ["localhost", "127.0.0.1"]
    configured_hosts = [host.strip() for host in trusted_hosts_str.split(",") if host.strip()]
    return list(set(default_hosts + configured_hosts))


def apply_security_middleware(app: FastAPI) -> None:
    """
    Applique tous les middlewares de sécurité à l'application FastAPI
    """
    # Configuration CORS
    cors_config = get_cors_config()
    app.add_middleware(
        CORSMiddleware,
        **cors_config
    )
    
    # Middleware des hôtes de confiance
    trusted_hosts = get_trusted_hosts()
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )


def add_security_headers(app: FastAPI) -> None:
    """
    Ajoute les headers de sécurité à toutes les réponses
    """
    @app.middleware("http")
    async def add_security_headers_middleware(request, call_next):
        response = await call_next(request)
        
        # Ajout des headers de sécurité
        security_headers = get_security_headers()
        for header, value in security_headers.items():
            if value is not None:
                response.headers[header] = value
            else:
                # Pour supprimer un header, on le définit à une chaîne vide
                # ou on utilise del si possible
                try:
                    del response.headers[header]
                except (KeyError, AttributeError):
                    # Si del n'est pas supporté, on définit à une chaîne vide
                    response.headers[header] = ""
        
        return response


def configure_security(app: FastAPI) -> None:
    """
    Configure complètement la sécurité de l'application
    """
    # Appliquer les middlewares de sécurité
    apply_security_middleware(app)
    
    # Ajouter les headers de sécurité
    add_security_headers(app)
    
    print("🔒 Configuration de sécurité appliquée")
    print(f"   - CORS Origins: {get_cors_config()['allow_origins']}")
    print(f"   - Trusted Hosts: {get_trusted_hosts()}")
    print(f"   - Security Headers: {len(get_security_headers())} headers configurés")
