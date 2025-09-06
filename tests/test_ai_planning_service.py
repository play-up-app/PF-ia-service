import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, time
from app.services.ai_planning_service import AIPlanningService
from app.models.models import AITournamentPlanning, Tournament, Team
import uuid


class TestAIPlanningService:
    """Tests pour le service AI Planning"""

    @pytest.fixture
    def mock_get_supabase(self):
        """Mock du client Supabase"""
        with patch('app.services.ai_planning_service.getSupabase') as mock_get_supabase:
            mock_client = Mock()
            mock_get_supabase.return_value = mock_client
            yield mock_get_supabase, mock_client

    @pytest.fixture
    def mock_tournament_data(self):
        """Données de tournoi de test"""
        tournament = Mock(spec=Tournament)
        tournament.name = "Tournoi Test"
        tournament.tournament_type = "round_robin"
        tournament.courts_available = 2
        tournament.start_date = date(2024, 6, 15)
        tournament.start_time = time(9, 0)
        tournament.match_duration_minutes = 15
        tournament.break_duration_minutes = 5
        tournament.status = "ready"
        
        team1 = Mock(spec=Team)
        team1.name = "Équipe 1"
        team2 = Mock(spec=Team)
        team2.name = "Équipe 2"
        team3 = Mock(spec=Team)
        team3.name = "Équipe 3"
        
        return {
            "tournament": tournament,
            "teams": [team1, team2, team3],
            "teams_count": 3,
            "has_minimum_teams": True,
            "can_start": True
        }

    @pytest.fixture
    def mock_ai_response(self):
        """Réponse AI de test"""
        return {
            "type_tournoi": "round_robin",
            "commentaires": "Planning généré avec succès",
            "matchs_round_robin": [
                {
                    "match_id": "rr_1",
                    "equipe_a": "Équipe 1",
                    "equipe_b": "Équipe 2",
                    "terrain": 1,
                    "debut_horaire": datetime(2024, 6, 15, 9, 0),
                    "fin_horaire": datetime(2024, 6, 15, 9, 15),
                    "journee": 1
                }
            ],
            "poules": [],
            "phase_elimination_apres_poules": None
        }

    @pytest.fixture
    def mock_planning_response(self):
        """Réponse de planning de test"""
        mock_planning = Mock(spec=AITournamentPlanning)
        mock_planning.id = "550e8400-e29b-41d4-a716-446655440001"
        mock_planning.tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        return mock_planning

    @pytest.fixture
    def service(self, mock_get_supabase):
        """Service AI Planning avec mocks"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        return AIPlanningService()

    def test_init(self, mock_get_supabase):
        """Test d'initialisation du service"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        service = AIPlanningService()
        assert service.supabase == mock_client
        assert service.openAIService is not None
        assert service.databaseService is not None
        assert service.tournamentService is not None

    def test_generate_planning_success(self, service, mock_get_supabase, mock_tournament_data, mock_ai_response, mock_planning_response):
        """Test de génération de planning avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock des services
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=True):
                with patch.object(service.openAIService, 'generate_planning', return_value=mock_ai_response):
                    with patch.object(service.databaseService, 'savePlanning', return_value=mock_planning_response):
                        with patch.object(service.databaseService, 'saveMatches', return_value=[Mock()]):
                            with patch.object(service.databaseService, 'savePoules', return_value=[]):
                                
                                result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                                
                                assert result is not None
                                assert result == mock_planning_response

    def test_generate_planning_no_tournament_data(self, service, mock_get_supabase):
        """Test de génération de planning sans données de tournoi"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=None):
            result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
            
            assert result is None

    def test_generate_planning_invalid_tournament_data(self, service, mock_get_supabase, mock_tournament_data):
        """Test de génération de planning avec données invalides"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=False):
                result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                
                assert result is None

    def test_generate_planning_openai_failure(self, service, mock_get_supabase, mock_tournament_data):
        """Test de génération de planning avec échec OpenAI"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=True):
                with patch.object(service.openAIService, 'generate_planning', return_value=None):
                    result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                    
                    assert result is None

    def test_generate_planning_save_planning_failure(self, service, mock_get_supabase, mock_tournament_data, mock_ai_response):
        """Test de génération de planning avec échec de sauvegarde du planning"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=True):
                with patch.object(service.openAIService, 'generate_planning', return_value=mock_ai_response):
                    with patch.object(service.databaseService, 'savePlanning', return_value=None):
                        result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                        
                        assert result is None

    def test_generate_planning_save_matches_failure(self, service, mock_get_supabase, mock_tournament_data, mock_ai_response, mock_planning_response):
        """Test de génération de planning avec échec de sauvegarde des matchs"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=True):
                with patch.object(service.openAIService, 'generate_planning', return_value=mock_ai_response):
                    with patch.object(service.databaseService, 'savePlanning', return_value=mock_planning_response):
                        with patch.object(service.databaseService, 'saveMatches', return_value=None):
                            with patch.object(service, '_deletePlanning', return_value=True):
                                result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                                
                                assert result is None

    def test_generate_planning_save_poules_failure(self, service, mock_get_supabase, mock_tournament_data, mock_ai_response, mock_planning_response):
        """Test de génération de planning avec échec de sauvegarde des poules"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', return_value=mock_tournament_data):
            with patch.object(service.tournamentService, '_validateTournamentData', return_value=True):
                with patch.object(service.openAIService, 'generate_planning', return_value=mock_ai_response):
                    with patch.object(service.databaseService, 'savePlanning', return_value=mock_planning_response):
                        with patch.object(service.databaseService, 'saveMatches', return_value=[Mock()]):
                            with patch.object(service.databaseService, 'savePoules', return_value=None):
                                with patch.object(service, '_deletePlanning', return_value=True):
                                    result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
                                    
                                    assert result is None

    def test_generate_planning_exception(self, service, mock_get_supabase):
        """Test de génération de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service.tournamentService, 'getTournamentWithTeams', side_effect=Exception("Test error")):
            result = service.generatePlanning("550e8400-e29b-41d4-a716-446655440000")
            
            assert result is None

    def test_get_planning_status_success(self, service, mock_get_supabase):
        """Test de récupération du statut de planning avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock(data=[{"status": "generated"}])
        
        result = service.getPlanningStatus("550e8400-e29b-41d4-a716-446655440001")
        
        assert result == "generated"

    def test_get_planning_status_not_found(self, service, mock_get_supabase):
        """Test de récupération du statut de planning inexistant"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête sans données
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock(data=[])
        
        result = service.getPlanningStatus("550e8400-e29b-41d4-a716-446655440999")
        
        assert result is None

    def test_get_planning_status_exception(self, service, mock_get_supabase):
        """Test de récupération du statut de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.side_effect = Exception("Database error")
        
        result = service.getPlanningStatus("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is None

    def test_regenerate_planning_success(self, service, mock_get_supabase, mock_tournament_data, mock_ai_response, mock_planning_response):
        """Test de régénération de planning avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de l'ancien planning
        old_planning = Mock(spec=AITournamentPlanning)
        old_planning.tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch.object(service, '_getPlanningById', return_value=old_planning):
            with patch.object(service, '_deletePlanning', return_value=True):
                with patch.object(service, 'generatePlanning', return_value=mock_planning_response):
                    result = service.regeneratePlanning("550e8400-e29b-41d4-a716-446655440001")
                    
                    assert result is not None
                    assert result == mock_planning_response

    def test_regenerate_planning_no_old_planning(self, service, mock_get_supabase):
        """Test de régénération de planning sans ancien planning"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service, '_getPlanningById', return_value=None):
            result = service.regeneratePlanning("550e8400-e29b-41d4-a716-446655440001")
            
            assert result is None

    def test_regenerate_planning_exception(self, service, mock_get_supabase):
        """Test de régénération de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        with patch.object(service, '_getPlanningById', side_effect=Exception("Test error")):
            result = service.regeneratePlanning("550e8400-e29b-41d4-a716-446655440001")
            
            assert result is None

    def test_build_static_prompt(self, service, mock_tournament_data):
        """Test de construction du prompt statique"""
        result = service._buildStaticPrompt(mock_tournament_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert "Tournoi Test" in result
        assert "round_robin" in result
        assert "Équipe 1" in result
        assert "Équipe 2" in result
        assert "Équipe 3" in result
        assert "2" in result  # courts_available
        assert "15" in result  # match_duration_minutes
        assert "5" in result  # break_duration_minutes

    def test_delete_planning_success(self, service, mock_get_supabase):
        """Test de suppression de planning"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock des suppressions
        mock_table = Mock()
        mock_delete_matches = Mock()
        mock_delete_poules = Mock()
        mock_delete_planning = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete_matches
        mock_delete_matches.eq.return_value = mock_delete_matches
        mock_delete_matches.execute.return_value = Mock()
        
        result = service._deletePlanning("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is True

    def test_delete_planning_exception(self, service, mock_get_supabase):
        """Test de suppression de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_table.delete.side_effect = Exception("Database error")
        
        result = service._deletePlanning("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is False

    def test_get_planning_by_id_success(self, service, mock_get_supabase, mock_planning_response):
        """Test de récupération de planning par ID"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock(data=[{
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "tournament_id": "550e8400-e29b-41d4-a716-446655440000",
            "type_tournoi": "round_robin",
            "status": "generated",
            "planning_data": {},
            "total_matches": 1,
            "ai_comments": "Test planning",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }])
        
        result = service._getPlanningById("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is not None

    def test_get_planning_by_id_not_found(self, service, mock_get_supabase):
        """Test de récupération de planning inexistant"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête sans données
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock(data=[])
        
        result = service._getPlanningById("550e8400-e29b-41d4-a716-446655440999")
        
        assert result is None

    def test_get_planning_by_id_exception(self, service, mock_get_supabase):
        """Test de récupération de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.side_effect = Exception("Database error")
        
        result = service._getPlanningById("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is None

    def test_delete_planning_by_tournament_id_success(self, service, mock_get_supabase):
        """Test de suppression de planning par ID de tournoi"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock des transactions
        mock_transaction = Mock()
        mock_client.transaction.return_value = mock_transaction
        
        result = service._deletePlanningByTournamentId("550e8400-e29b-41d4-a716-446655440000")
        
        assert result is True

    def test_delete_planning_by_tournament_id_exception(self, service, mock_get_supabase):
        """Test de suppression de planning par tournoi avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_client.transaction.side_effect = Exception("Database error")
        
        result = service._deletePlanningByTournamentId("550e8400-e29b-41d4-a716-446655440000")
        
        assert result is False
