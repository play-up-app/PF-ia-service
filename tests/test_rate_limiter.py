import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.rate_limiter import get_rate_limit_config, limiter
from main import app

client = TestClient(app)


class TestRateLimiter:
    """Tests pour le rate limiting"""

    def test_rate_limit_config_development(self):
        """Test de la configuration des limites en développement"""
        with patch("app.core.rate_limiter.settings") as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            config = get_rate_limit_config()

            assert config["default"] == "1000/minute"
            assert config["strict"] == "100/minute"
            assert config["generous"] == "5000/hour"

    def test_rate_limit_config_production(self):
        """Test de la configuration des limites en production"""
        with patch("app.core.rate_limiter.settings") as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            config = get_rate_limit_config()

            assert config["default"] == "100/minute"
            assert config["strict"] == "10/minute"
            assert config["generous"] == "500/hour"

    def test_rate_limit_on_generate_planning(self):
        """Test que le rate limiting est appliqué sur la génération de planning"""
        # Vérifier que le décorateur est présent
        from app.api.routes.planning import generate_planning

        # Le décorateur devrait être appliqué
        assert hasattr(generate_planning, "__wrapped__") or hasattr(
            generate_planning, "limiter"
        )

    def test_rate_limit_on_get_status(self):
        """Test que le rate limiting est appliqué sur la récupération de statut"""
        from app.api.routes.planning import get_planning_status

        # Le décorateur devrait être appliqué
        assert hasattr(get_planning_status, "__wrapped__") or hasattr(
            get_planning_status, "limiter"
        )

    def test_rate_limit_on_regenerate_planning(self):
        """Test que le rate limiting est appliqué sur la régénération de planning"""
        from app.api.routes.planning import regenerate_planning

        # Le décorateur devrait être appliqué
        assert hasattr(regenerate_planning, "__wrapped__") or hasattr(
            regenerate_planning, "limiter"
        )

    def test_rate_limit_on_get_planning_by_id(self):
        """Test que le rate limiting est appliqué sur la récupération de planning par ID"""
        from app.api.routes.planning import get_planning_by_id

        # Le décorateur devrait être appliqué
        assert hasattr(get_planning_by_id, "__wrapped__") or hasattr(
            get_planning_by_id, "limiter"
        )

    def test_rate_limit_on_get_planning_by_tournament_id(self):
        """Test que le rate limiting est appliqué sur la récupération de planning par tournoi"""
        from app.api.routes.planning import get_planning_by_tournament_id

        # Le décorateur devrait être appliqué
        assert hasattr(get_planning_by_tournament_id, "__wrapped__") or hasattr(
            get_planning_by_tournament_id, "limiter"
        )

    def test_limiter_instance(self):
        """Test que l'instance du limiter est correctement configurée"""
        assert limiter is not None
        assert hasattr(limiter, "limit")

    def test_rate_limit_exceeded_handler_exists(self):
        """Test que le gestionnaire de dépassement de limite existe"""
        from app.core.rate_limiter import rate_limit_exceeded_handler

        # Vérifier que la fonction existe
        assert callable(rate_limit_exceeded_handler)
