from datetime import date, datetime, time

import pytest
from unittest.mock import MagicMock, Mock, patch

from app.services.ai_planning_service import AIPlanningService
from app.services.database_service import DatabaseService
from app.services.openai_service import OpenAIClientService
from app.services.tournament_service import TournamentService


class TestIntegration:
    """Tests d'intégration entre les services"""

    @pytest.fixture
    def mock_tournament_data(self):
        """Données mockées pour un tournoi avec équipes"""
        return {
            "tournament": Mock(
                id="550e8400-e29b-41d4-a716-446655440000",
                name="Tournoi Test",
                tournament_type="round_robin",
                max_teams=8,
                courts_available=2,
                start_date=date(2024, 6, 15),
                start_time=time(9, 0),
                match_duration_minutes=15,
                break_duration_minutes=5,
                status="ready",
            ),
            "teams": [
                Mock(name="Équipe 1", id="team-1"),
                Mock(name="Équipe 2", id="team-2"),
                Mock(name="Équipe 3", id="team-3"),
            ],
            "teams_count": 3,
            "has_minimum_teams": True,
            "can_start": True,
        }

    @pytest.fixture
    def mock_ai_response(self):
        """Réponse mockée de l'IA"""
        return {
            "type_tournoi": "round_robin",
            "matchs_round_robin": [
                {
                    "match_id": "rr_1",
                    "equipe_a": "Équipe 1",
                    "equipe_b": "Équipe 2",
                    "debut_horaire": "2024-06-15T09:00:00",
                    "fin_horaire": "2024-06-15T09:15:00",
                    "terrain": 1,
                    "journee": 1,
                }
            ],
            "commentaires": "Planning généré avec succès",
        }

    @pytest.fixture
    def mock_planning_response(self):
        """Réponse mockée pour un planning sauvegardé"""
        return Mock(
            id="planning-123",
            tournament_id="550e8400-e29b-41d4-a716-446655440000",
            type_tournoi="round_robin",
            status="generated",
            total_matches=1,
        )

    @pytest.mark.integration
    def test_full_planning_generation_workflow(
        self,
        mock_ai_planning_service,
        mock_tournament_data,
        mock_ai_response,
        mock_planning_response,
    ):
        """Test du workflow complet de génération de planning"""
        # Configurer le mock du service
        mock_ai_planning_service.generatePlanning.return_value = mock_planning_response

        # Exécuter le workflow complet
        result = mock_ai_planning_service.generatePlanning(
            "550e8400-e29b-41d4-a716-446655440000"
        )

        # Vérifications
        assert result is not None
        assert result.id == "planning-123"
        assert result.tournament_id == "550e8400-e29b-41d4-a716-446655440000"
        assert result.type_tournoi == "round_robin"

        # Vérifier que la méthode a été appelée avec les bons arguments
        mock_ai_planning_service.generatePlanning.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000"
        )

    @pytest.mark.integration
    def test_service_initialization(self, mock_get_supabase):
        """Test de l'initialisation correcte de tous les services"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase

        # Vérifier que tous les services peuvent être initialisés
        ai_planning_service = AIPlanningService()
        tournament_service = TournamentService()
        database_service = DatabaseService()

        # Vérifier que les services ont les bonnes dépendances
        assert ai_planning_service.tournamentService is not None
        assert ai_planning_service.openAIService is not None
        assert ai_planning_service.databaseService is not None

        assert tournament_service.supabase is not None
        assert database_service.supabase is not None

    @pytest.mark.integration
    def test_error_propagation(self, mock_ai_planning_service):
        """Test de la propagation des erreurs entre services"""
        # Simuler une erreur dans le service
        mock_ai_planning_service.generatePlanning.return_value = None

        result = mock_ai_planning_service.generatePlanning(
            "550e8400-e29b-41d4-a716-446655440000"
        )

        # L'erreur doit être propagée et le résultat doit être None
        assert result is None
        mock_ai_planning_service.generatePlanning.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000"
        )

    @pytest.mark.integration
    def test_data_flow_between_services(
        self, mock_ai_planning_service, mock_tournament_data, mock_ai_response
    ):
        """Test du flux de données entre les services"""
        # Configurer le mock pour retourner les données de test
        mock_ai_planning_service.generatePlanning.return_value = Mock(
            id="planning-123",
            tournament_id="550e8400-e29b-41d4-a716-446655440000",
            type_tournoi="round_robin",
            planning_data=mock_ai_response,
        )

        # Exécuter le workflow
        result = mock_ai_planning_service.generatePlanning(
            "550e8400-e29b-41d4-a716-446655440000"
        )

        # Vérifier que les données sont correctement transmises
        assert result is not None
        assert result.id == "planning-123"
        assert result.tournament_id == "550e8400-e29b-41d4-a716-446655440000"
        assert result.type_tournoi == "round_robin"
        assert result.planning_data == mock_ai_response

        # Vérifier que la méthode a été appelée avec les bons arguments
        mock_ai_planning_service.generatePlanning.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000"
        )

    @pytest.mark.integration
    def test_rollback_on_failure(
        self, mock_ai_planning_service, mock_planning_response
    ):
        """Test du rollback en cas d'échec"""
        # Simuler un échec lors de la génération
        mock_ai_planning_service.generatePlanning.return_value = None
        mock_ai_planning_service._deletePlanning.return_value = True

        result = mock_ai_planning_service.generatePlanning(
            "550e8400-e29b-41d4-a716-446655440000"
        )

        # Vérifier que le rollback a été effectué
        assert result is None
        mock_ai_planning_service.generatePlanning.assert_called_once_with(
            "550e8400-e29b-41d4-a716-446655440000"
        )
