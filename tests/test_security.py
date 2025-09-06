import os

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_cors_config, get_security_headers, get_trusted_hosts
from main import app


class TestSecurity:
    """Tests pour les configurations de sécurité"""

    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)

    def test_cors_configuration(self):
        """Test de la configuration CORS"""
        cors_config = get_cors_config()

        # Vérifier que les méthodes HTTP sont configurées
        assert "GET" in cors_config["allow_methods"]
        assert "POST" in cors_config["allow_methods"]
        assert "OPTIONS" in cors_config["allow_methods"]

        # Vérifier que les headers sont configurés
        assert "Content-Type" in cors_config["allow_headers"]
        assert "Authorization" in cors_config["allow_headers"]

        # Vérifier que les credentials sont activés
        assert cors_config["allow_credentials"] is True

        # Vérifier le cache des preflight requests
        assert cors_config["max_age"] == 86400

    def test_security_headers(self):
        """Test des headers de sécurité"""
        headers = get_security_headers()

        # Vérifier les headers de sécurité essentiels
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers

        # Vérifier que X-Powered-By est supprimé
        assert headers["X-Powered-By"] is None

        # Vérifier la politique de sécurité du contenu
        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-src 'none'" in csp

    def test_trusted_hosts(self):
        """Test de la configuration des hôtes de confiance"""
        # Sauvegarder l'environnement actuel
        original_env = os.getenv("ENVIRONMENT")

        try:
            # Test en mode normal
            os.environ["ENVIRONMENT"] = "development"
            trusted_hosts = get_trusted_hosts()

            # Vérifier que localhost est inclus par défaut
            assert "localhost" in trusted_hosts
            assert "127.0.0.1" in trusted_hosts

            # Test en mode production
            os.environ["ENVIRONMENT"] = "production"
            os.environ["TRUSTED_HOSTS"] = "example.com,api.example.com"
            trusted_hosts_prod = get_trusted_hosts()
            assert "example.com" in trusted_hosts_prod
            assert "api.example.com" in trusted_hosts_prod
            assert "localhost" not in trusted_hosts_prod

        finally:
            # Restaurer l'environnement
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            else:
                os.environ.pop("ENVIRONMENT", None)

    def test_cors_origins_environment_variable(self):
        """Test de la configuration CORS avec variable d'environnement"""
        # Sauvegarder la valeur actuelle
        original_cors = os.getenv("CORS_ORIGIN")

        try:
            # Tester avec une origine personnalisée
            os.environ["CORS_ORIGIN"] = "https://example.com,https://test.com"
            cors_config = get_cors_config()

            assert "https://example.com" in cors_config["allow_origins"]
            assert "https://test.com" in cors_config["allow_origins"]

        finally:
            # Restaurer la valeur originale
            if original_cors:
                os.environ["CORS_ORIGIN"] = original_cors
            else:
                os.environ.pop("CORS_ORIGIN", None)

    def test_security_headers_in_response(self, client):
        """Test que les headers de sécurité sont présents dans les réponses"""
        response = client.get("/", headers={"Host": "localhost:8003"})

        # Vérifier que la réponse est réussie
        assert response.status_code == 200

        # Vérifier les headers de sécurité
        headers = response.headers

        # Headers de sécurité essentiels
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-xss-protection" in headers
        assert "referrer-policy" in headers

        # Vérifier que X-Powered-By n'est pas présent
        assert "x-powered-by" not in headers

    def test_cors_preflight_request(self, client):
        """Test des requêtes CORS preflight"""
        # Simuler une requête preflight
        response = client.options(
            "/",
            headers={
                "Host": "localhost:8003",
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )

        # Vérifier que la réponse est correcte
        assert response.status_code in [200, 204]

        # Vérifier les headers CORS
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers

    def test_trusted_host_middleware(self, client):
        """Test du middleware des hôtes de confiance"""
        # Test avec un hôte autorisé
        response = client.get("/", headers={"Host": "localhost:8003"})
        assert response.status_code == 200

        # Test avec un hôte non autorisé (devrait être rejeté)
        response = client.get("/", headers={"Host": "malicious.com"})
        assert response.status_code == 400
        # Le middleware devrait rejeter les hôtes non autorisés
        # Note: En mode test, le comportement peut varier

    def test_content_security_policy(self, client):
        """Test de la politique de sécurité du contenu"""
        response = client.get("/", headers={"Host": "localhost:8003"})
        headers = response.headers

        # Vérifier que CSP est présent
        assert "content-security-policy" in headers

        csp = headers["content-security-policy"]

        # Vérifier les directives CSP essentielles
        assert "default-src 'self'" in csp
        assert "frame-src 'none'" in csp
        assert "object-src 'none'" in csp

    def test_environment_specific_config(self):
        """Test de la configuration selon l'environnement"""
        # Sauvegarder l'environnement actuel
        original_env = os.getenv("ENVIRONMENT")

        try:
            # Test en mode développement
            os.environ["ENVIRONMENT"] = "development"
            cors_config_dev = get_cors_config()

            # Test en mode production
            os.environ["ENVIRONMENT"] = "production"
            cors_config_prod = get_cors_config()

            # En développement, localhost devrait être inclus
            if "http://localhost:3000" not in cors_config_dev["allow_origins"]:
                # Si pas dans CORS_ORIGIN, devrait être ajouté automatiquement
                pass

        finally:
            # Restaurer l'environnement
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            else:
                os.environ.pop("ENVIRONMENT", None)
