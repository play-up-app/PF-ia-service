import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, time
from app.services.tournament_service import TournamentService
from app.models.models import Tournament, Team

class TestTournamentService:
    """Tests unitaires pour TournamentService"""

    @pytest.fixture
    def service(self, mock_get_supabase):
        """Instance du service avec mocks"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        return TournamentService(supabase_client=mock_client)

    @pytest.fixture
    def mock_tournament_data(self):
        """Données mockées pour un tournoi"""
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Tournoi Test",
            "description": "Tournoi de test",
            "tournament_type": "round_robin",
            "max_teams": 8,
            "courts_available": 2,
            "start_date": date(2024, 6, 15),
            "start_time": time(9, 0),
            "match_duration_minutes": 15,
            "break_duration_minutes": 5,
            "constraints": {},
            "organizer_id": "550e8400-e29b-41d4-a716-446655440001",
            "status": "ready",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    @pytest.fixture
    def mock_team_data(self):
        """Données mockées pour une équipe"""
        return {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Équipe Test",
            "description": "Équipe de test",
            "tournament_id": "550e8400-e29b-41d4-a716-446655440000",
            "captain_id": "550e8400-e29b-41d4-a716-446655440003",
            "status": "registered",
            "contact_email": "test@example.com",
            "contact_phone": "0123456789",
            "skill_level": "intermediate",
            "notes": "Notes de test",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    def test_get_tournament_by_id_success(self, service, mock_get_supabase, mock_tournament_data):
        """Test de récupération d'un tournoi par ID avec succès"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Créer un objet simple qui simule la réponse de Supabase
        class MockSupabaseResponse:
            def __init__(self, data):
                self.data = data
        
                # Créer un mock qui retourne directement les bonnes données
        def mock_execute(*args, **kwargs):
            return MockSupabaseResponse(mock_tournament_data)
    
        def mock_single(*args, **kwargs):
            return type('MockSingle', (), {'execute': mock_execute})()
    
        def mock_eq(*args, **kwargs):
            return type('MockEq', (), {'single': mock_single})()
    
        def mock_select(*args, **kwargs):
            return type('MockSelect', (), {'eq': mock_eq})()
    
        def mock_table(*args, **kwargs):
            return type('MockTable', (), {'select': mock_select})()
        
        # Configurer le mock client pour retourner les bonnes données
        def table_side_effect(table_name):
            if table_name == "tournament":
                return mock_table()
            elif table_name == "team":
                                # Mock pour les équipes (vide)
                def mock_teams_execute(*args, **kwargs):
                    return MockSupabaseResponse([])
    
                def mock_teams_order(*args, **kwargs):
                    return type('MockOrder', (), {'execute': mock_teams_execute})()
    
                def mock_teams_eq(*args, **kwargs):
                    return type('MockEq', (), {'order': mock_teams_order})()
    
                def mock_teams_select(*args, **kwargs):
                    return type('MockSelect', (), {'eq': mock_teams_eq})()
    
                def mock_teams_table(*args, **kwargs):
                    return type('MockTable', (), {'select': mock_teams_select})()
                
                return mock_teams_table()
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentById(tournament_id)
        
        assert result is not None
        assert result.name == "Tournoi Test"
        assert result.tournament_type == "round_robin"
        assert result.registered_teams == 0

    def test_get_tournament_by_id_not_found(self, service, mock_get_supabase):
        """Test de récupération d'un tournoi inexistant"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440999"
        
        class MockSupabaseResponse:
            def __init__(self, data):
                self.data = data
        
        # Mock de la requête sans données
        def mock_execute():
            return MockSupabaseResponse(None)
        
        def mock_single():
            return type('MockSingle', (), {'execute': mock_execute})()
        
        def mock_eq(*args):
            return type('MockEq', (), {'single': mock_single})()
        
        def mock_select(*args):
            return type('MockSelect', (), {'eq': mock_eq})()
        
        def mock_table():
            return type('MockTable', (), {'select': mock_select})()
        
        def table_side_effect(table_name):
            return mock_table()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentById(tournament_id)
        
        assert result is None

    def test_get_tournament_by_id_exception(self, service, mock_get_supabase):
        """Test de récupération avec exception"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock d'exception
        def table_side_effect(table_name):
            mock_table = MagicMock()
            mock_table.select.side_effect = Exception("Database error")
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentById(tournament_id)
        
        assert result is None

    def test_get_tournament_teams_success(self, service, mock_get_supabase, mock_team_data):
        """Test de récupération des équipes d'un tournoi"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        class MockSupabaseResponse:
            def __init__(self, data):
                self.data = data
        
                # Mock de la requête équipes
        def mock_execute(*args, **kwargs):
            return MockSupabaseResponse([mock_team_data])
    
        def mock_order(*args, **kwargs):
            return type('MockOrder', (), {'execute': mock_execute})()
    
        def mock_eq(*args, **kwargs):
            return type('MockEq', (), {'order': mock_order})()
    
        def mock_select(*args, **kwargs):
            return type('MockSelect', (), {'eq': mock_eq})()
    
        def mock_table(*args, **kwargs):
            return type('MockTable', (), {'select': mock_select})()
        
        def table_side_effect(table_name):
            return mock_table()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentTeams(tournament_id)
        
        assert len(result) == 1
        assert result[0].name == "Équipe Test"
        assert result[0].tournament_id == tournament_id

    def test_get_tournament_teams_empty(self, service, mock_get_supabase):
        """Test de récupération des équipes d'un tournoi sans équipes"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        class MockSupabaseResponse:
            def __init__(self, data):
                self.data = data
        
        # Mock de la requête équipes vide
        def mock_execute():
            return MockSupabaseResponse([])
        
        def mock_order(*args):
            return type('MockOrder', (), {'execute': mock_execute})()
        
        def mock_eq(*args):
            return type('MockEq', (), {'order': mock_order})()
        
        def mock_select(*args):
            return type('MockSelect', (), {'eq': mock_eq})()
        
        def mock_table():
            return type('MockTable', (), {'select': mock_select})()
        
        def table_side_effect(table_name):
            return mock_table()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentTeams(tournament_id)
        
        assert len(result) == 0

    def test_get_tournament_teams_exception(self, service, mock_get_supabase):
        """Test de récupération des équipes avec exception"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock d'exception
        def table_side_effect(table_name):
            mock_table = MagicMock()
            mock_table.select.side_effect = Exception("Database error")
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentTeams(tournament_id)
        
        assert result == []

    def test_get_tournament_with_teams_success(self, service, mock_get_supabase, mock_tournament_data, mock_team_data):
        """Test de récupération d'un tournoi avec ses équipes"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        class MockSupabaseResponse:
            def __init__(self, data):
                self.data = data
        
        # Configurer les mocks pour retourner les bonnes structures
        def table_side_effect(table_name):
            if table_name == "tournament":
                # Mock pour la requête tournoi
                def mock_execute(*args, **kwargs):
                    return MockSupabaseResponse(mock_tournament_data)
    
                def mock_single(*args, **kwargs):
                    return type('MockSingle', (), {'execute': mock_execute})()
    
                def mock_eq(*args, **kwargs):
                    return type('MockEq', (), {'single': mock_single})()
    
                def mock_select(*args, **kwargs):
                    return type('MockSelect', (), {'eq': mock_eq})()
    
                def mock_table(*args, **kwargs):
                    return type('MockTable', (), {'select': mock_select})()
    
                return mock_table()
    
            elif table_name == "team":
                # Mock pour la requête équipes
                def mock_execute(*args, **kwargs):
                    return MockSupabaseResponse([mock_team_data])
    
                def mock_order(*args, **kwargs):
                    return type('MockOrder', (), {'execute': mock_execute})()
    
                def mock_eq(*args, **kwargs):
                    return type('MockEq', (), {'order': mock_order})()
    
                def mock_select(*args, **kwargs):
                    return type('MockSelect', (), {'eq': mock_eq})()
    
                def mock_table(*args, **kwargs):
                    return type('MockTable', (), {'select': mock_select})()
    
                return mock_table()
            
            return MagicMock()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentWithTeams(tournament_id)
        
        assert result is not None
        assert "tournament" in result
        assert "teams" in result
        assert result["teams_count"] == 1

    def test_get_tournament_with_teams_no_tournament(self, service, mock_get_supabase):
        """Test de récupération d'un tournoi inexistant avec équipes"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440999"
        
        # Mock de la requête tournoi sans données
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        
        mock_result = Mock()
        mock_result.data = None
        mock_execute.return_value = mock_result
        
        def table_side_effect(table_name):
            mock_table = Mock()
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.single.return_value = mock_single
            mock_single.execute.return_value = mock_execute
            return mock_table
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentWithTeams(tournament_id)
        
        assert result is None

    def test_get_tournament_with_teams_no_teams(self, service, mock_get_supabase, mock_tournament_data):
        """Test de récupération d'un tournoi sans équipes"""
        mock_get_supabase_func, mock_client, mock_table = mock_get_supabase
        
        tournament_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock de la requête tournoi
        mock_tournament_select = Mock()
        mock_tournament_eq = Mock()
        mock_tournament_single = Mock()
        mock_tournament_execute = Mock()
        
        # Mock de la requête équipes vide
        mock_teams_select = Mock()
        mock_teams_eq = Mock()
        mock_teams_order = Mock()
        mock_teams_execute = Mock()
        
        # Configurer les chaînes de mocks
        mock_tournament_result = Mock()
        mock_tournament_result.data = mock_tournament_data
        mock_tournament_execute.return_value = mock_tournament_result
        
        mock_teams_result = Mock()
        mock_teams_result.data = []
        mock_teams_execute.return_value = mock_teams_result
        
        def table_side_effect(table_name):
            if table_name == "tournament":
                mock_table = Mock()
                mock_table.select.return_value = mock_tournament_select
                mock_tournament_select.eq.return_value = mock_tournament_eq
                mock_tournament_eq.single.return_value = mock_tournament_single
                mock_tournament_single.execute.return_value = mock_tournament_execute
                return mock_table
            elif table_name == "team":
                mock_table = Mock()
                mock_table.select.return_value = mock_teams_select
                mock_teams_select.eq.return_value = mock_teams_eq
                mock_teams_eq.order.return_value = mock_teams_order
                mock_teams_order.execute.return_value = mock_teams_execute
                return mock_table
            return Mock()
        
        mock_client.table.side_effect = table_side_effect
        
        result = service.getTournamentWithTeams(tournament_id)
        
        assert result is None

    def test_validate_tournament_data_valid(self, service):
        """Test de validation de données de tournoi valides"""
        tournament_data = {
            "tournament": Mock(
                max_teams=8,
                courts_available=2,
                tournament_type="round_robin",
                status="ready"
            ),
            "teams": [Mock(), Mock(), Mock()]  # 3 équipes
        }
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is True

    def test_validate_tournament_data_insufficient_teams(self, service):
        """Test de validation avec équipes insuffisantes"""
        tournament_data = {
            "tournament": Mock(
                max_teams=8,
                courts_available=2,
                tournament_type="round_robin"
            ),
            "teams": [Mock()]  # 1 équipe seulement
        }
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is False

    def test_validate_tournament_data_too_many_teams(self, service):
        """Test de validation avec trop d'équipes"""
        tournament_data = {
            "tournament": Mock(
                max_teams=2,
                courts_available=2,
                tournament_type="round_robin"
            ),
            "teams": [Mock(), Mock(), Mock()]  # 3 équipes pour max 2
        }
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is False

    def test_validate_tournament_data_no_courts(self, service):
        """Test de validation sans terrains"""
        tournament_data = {
            "tournament": Mock(
                max_teams=8,
                courts_available=0,
                tournament_type="round_robin"
            ),
            "teams": [Mock(), Mock()]
        }
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is False

    def test_validate_tournament_data_no_type(self, service):
        """Test de validation sans type de tournoi"""
        tournament_data = {
            "tournament": Mock(
                max_teams=8,
                courts_available=2,
                tournament_type=None
            ),
            "teams": [Mock(), Mock()]
        }
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is False

    def test_validate_tournament_data_exception(self, service):
        """Test de validation avec exception"""
        tournament_data = {
            "tournament": Mock(),
            "teams": Mock()
        }
        
        # Mock d'exception lors de l'accès aux propriétés
        tournament_data["tournament"].max_teams.side_effect = Exception("Error")
        
        result = service._validateTournamentData(tournament_data)
        
        assert result is False




