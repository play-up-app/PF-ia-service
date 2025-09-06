import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, time
from app.services.database_service import DatabaseService
from app.models.models import AITournamentPlanning, AIPlanningData, AIGeneratedMatch, AIGeneratedPoule, Match
import uuid


class TestDatabaseService:
    """Tests pour le service Database"""

    @pytest.fixture
    def mock_get_supabase(self):
        """Mock du client Supabase"""
        with patch('app.services.database_service.getSupabase') as mock_get_supabase:
            mock_client = Mock()
            mock_get_supabase.return_value = mock_client
            yield mock_get_supabase, mock_client

    @pytest.fixture
    def service(self, mock_get_supabase):
        """Service Database avec mocks"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        return DatabaseService()

    @pytest.fixture
    def mock_planning_data(self):
        """Données de planning de test"""
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
        return {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "tournament_id": "550e8400-e29b-41d4-a716-446655440000",
            "type_tournoi": "round_robin",
            "status": "generated",
            "planning_data": {},
            "total_matches": 1,
            "ai_comments": "Planning généré avec succès",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }

    def test_init(self, mock_get_supabase):
        """Test d'initialisation du service"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        service = DatabaseService()
        assert service.supabase == mock_client

    def test_save_planning_success(self, service, mock_get_supabase, mock_planning_data, mock_planning_response):
        """Test de sauvegarde de planning avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de l'insertion
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[mock_planning_response])
        
        result = service.savePlanning("550e8400-e29b-41d4-a716-446655440000", mock_planning_data, "round_robin")
        
        assert result is not None
        assert isinstance(result, AITournamentPlanning)
        assert result.id == "550e8400-e29b-41d4-a716-446655440001"
        mock_table.insert.assert_called_once()

    def test_save_planning_exception(self, service, mock_get_supabase, mock_planning_data):
        """Test de sauvegarde de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_insert = Mock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.side_effect = Exception("Database error")
        
        result = service.savePlanning("550e8400-e29b-41d4-a716-446655440000", mock_planning_data, "round_robin")
        
        assert result is None

    def test_save_matches_success(self, service, mock_get_supabase, mock_planning_data):
        """Test de sauvegarde de matchs avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la récupération du mapping des équipes
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        # Mock de la récupération du tournament_id
        mock_planning_select = Mock()
        mock_planning_eq = Mock()
        mock_planning_single = Mock()
        mock_planning_execute = Mock()
        
        mock_table.select.return_value = mock_planning_select
        mock_planning_select.eq.return_value = mock_planning_eq
        mock_planning_eq.single.return_value = mock_planning_single
        mock_planning_single.execute.return_value = Mock(data={"tournament_id": "550e8400-e29b-41d4-a716-446655440000"})
        
        # Mock de la récupération des équipes
        mock_teams_select = Mock()
        mock_teams_eq = Mock()
        mock_teams_execute = Mock()
        
        # Utiliser side_effect pour retourner différents mocks selon l'appel
        mock_table.select.side_effect = [mock_planning_select, mock_teams_select]
        mock_teams_select.eq.return_value = mock_teams_eq
        mock_teams_eq.execute.return_value = Mock(data=[
            {"name": "Équipe 1", "id": "550e8400-e29b-41d4-a716-446655440002"},
            {"name": "Équipe 2", "id": "550e8400-e29b-41d4-a716-446655440003"}
        ])
        
        # Mock de l'insertion des matchs
        mock_matches_insert = Mock()
        mock_matches_execute = Mock()
        
        mock_table.insert.return_value = mock_matches_insert
        mock_matches_insert.execute.return_value = Mock(data=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "planning_id": "550e8400-e29b-41d4-a716-446655440001",
                "match_id_ai": "rr_1",
                "equipe_a": "Équipe 1",
                "equipe_b": "Équipe 2",
                "terrain": 1,
                "debut_horaire": "2024-06-15T09:00:00",
                "fin_horaire": "2024-06-15T09:15:00",
                "phase": "round_robin",
                "journee": 1,
                "status": "scheduled",
                "resolved_equipe_a_id": "550e8400-e29b-41d4-a716-446655440002",
                "resolved_equipe_b_id": "550e8400-e29b-41d4-a716-446655440003",
                "created_at": "2024-01-01T00:00:00"
            }
        ])
        
        result = service.saveMatches("550e8400-e29b-41d4-a716-446655440001", mock_planning_data)
        
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], AIGeneratedMatch)

    def test_save_matches_no_teams_mapping(self, service, mock_get_supabase, mock_planning_data):
        """Test de sauvegarde de matchs sans mapping d'équipes"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la récupération du mapping des équipes qui échoue
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.side_effect = Exception("Database error")
        
        result = service.saveMatches("550e8400-e29b-41d4-a716-446655440001", mock_planning_data)
        
        assert result is None

    def test_save_matches_exception(self, service, mock_get_supabase, mock_planning_data):
        """Test de sauvegarde de matchs avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la récupération du mapping des équipes
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = Mock(data={"tournament_id": "550e8400-e29b-41d4-a716-446655440000"})
        
        # Mock de l'insertion qui échoue
        mock_insert = Mock()
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.side_effect = Exception("Insert error")
        
        result = service.saveMatches("550e8400-e29b-41d4-a716-446655440001", mock_planning_data)
        
        assert result is None

    def test_save_poules_success(self, service, mock_get_supabase):
        """Test de sauvegarde de poules avec succès"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        planning_data = {
            "type_tournoi": "poules_elimination",
            "poules": [
                {
                    "poule_id": "poule_a",
                    "nom_poule": "Poule A",
                    "equipes": ["Équipe 1", "Équipe 2"],
                    "matchs": []
                }
            ],
            "commentaires": "Planning avec poules"
        }
        
        # Mock de l'insertion des poules
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[
            {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "planning_id": "550e8400-e29b-41d4-a716-446655440001",
                "poule_id": "poule_a",
                "nom_poule": "Poule A",
                "equipes": ["Équipe 1", "Équipe 2"],
                "nb_equipes": 2,
                "nb_matches": 0,
                "created_at": "2024-01-01T00:00:00"
            }
        ])
        
        result = service.savePoules("550e8400-e29b-41d4-a716-446655440001", planning_data)
        
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], AIGeneratedPoule)

    def test_save_poules_no_poules(self, service, mock_get_supabase):
        """Test de sauvegarde de poules sans poules"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        planning_data = {
            "type_tournoi": "round_robin",
            "poules": [],
            "commentaires": "Planning sans poules"
        }
        
        result = service.savePoules("550e8400-e29b-41d4-a716-446655440001", planning_data)
        
        assert result == []

    def test_save_poules_exception(self, service, mock_get_supabase):
        """Test de sauvegarde de poules avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        planning_data = {
            "type_tournoi": "poules_elimination",
            "poules": [
                {
                    "poule_id": "poule_a",
                    "nom_poule": "Poule A",
                    "equipes": ["Équipe 1", "Équipe 2"],
                    "matchs": []
                }
            ],
            "commentaires": "Planning avec poules"
        }
        
        # Mock d'exception
        mock_table = Mock()
        mock_insert = Mock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.side_effect = Exception("Database error")
        
        result = service.savePoules("550e8400-e29b-41d4-a716-446655440001", planning_data)
        
        assert result is None

    def test_get_planning_with_details_by_planning_id_success(self, service, mock_get_supabase, mock_planning_response):
        """Test de récupération de planning avec détails par ID"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête planning
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = Mock(data=mock_planning_response)
        
        result = service.getPlanningWithDetailsByPlanningId("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is not None
        assert isinstance(result, AITournamentPlanning)

    def test_get_planning_with_details_by_planning_id_not_found(self, service, mock_get_supabase):
        """Test de récupération de planning inexistant"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête sans données
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = Mock(data=None)
        
        result = service.getPlanningWithDetailsByPlanningId("550e8400-e29b-41d4-a716-446655440999")
        
        assert result is None

    def test_get_planning_with_details_by_planning_id_exception(self, service, mock_get_supabase):
        """Test de récupération de planning avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.side_effect = Exception("Database error")
        
        result = service.getPlanningWithDetailsByPlanningId("550e8400-e29b-41d4-a716-446655440001")
        
        assert result is None

    def test_get_planning_with_details_by_tournament_id_success(self, service, mock_get_supabase, mock_planning_response):
        """Test de récupération de planning par ID de tournoi"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête planning
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_limit = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[mock_planning_response])
        
        result = service.getPlanningWithDetailsByTournamentId("550e8400-e29b-41d4-a716-446655440000")
        
        assert result is not None
        assert isinstance(result, AITournamentPlanning)

    def test_get_planning_with_details_by_tournament_id_not_found(self, service, mock_get_supabase):
        """Test de récupération de planning par tournoi inexistant"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la requête sans données
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_limit = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[])
        
        with pytest.raises(Exception, match="Planning non trouve"):
            service.getPlanningWithDetailsByTournamentId("550e8400-e29b-41d4-a716-446655440999")

    def test_update_planning_status_success(self, service, mock_get_supabase):
        """Test de mise à jour du statut de planning"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la mise à jour
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_execute = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = Mock()
        
        result = service.updatePlanningStatus("550e8400-e29b-41d4-a716-446655440001", "completed")
        
        assert result is True
        mock_table.update.assert_called_once()

    def test_update_planning_status_exception(self, service, mock_get_supabase):
        """Test de mise à jour du statut avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.side_effect = Exception("Database error")
        
        result = service.updatePlanningStatus("550e8400-e29b-41d4-a716-446655440001", "completed")
        
        assert result is False

    def test_get_teams_mapping_success(self, service, mock_get_supabase):
        """Test de récupération du mapping des équipes"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock de la récupération du tournament_id
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        mock_planning_select = Mock()
        mock_planning_eq = Mock()
        mock_planning_single = Mock()
        mock_planning_execute = Mock()
        
        mock_table.select.return_value = mock_planning_select
        mock_planning_select.eq.return_value = mock_planning_eq
        mock_planning_eq.single.return_value = mock_planning_single
        mock_planning_single.execute.return_value = Mock(data={"tournament_id": "550e8400-e29b-41d4-a716-446655440000"})
        
        # Mock de la récupération des équipes
        mock_teams_select = Mock()
        mock_teams_eq = Mock()
        mock_teams_execute = Mock()
        
        # Utiliser side_effect pour retourner différents mocks selon l'appel
        mock_table.select.side_effect = [mock_planning_select, mock_teams_select]
        mock_teams_select.eq.return_value = mock_teams_eq
        mock_teams_eq.execute.return_value = Mock(data=[
            {"name": "Équipe 1", "id": "550e8400-e29b-41d4-a716-446655440002"},
            {"name": "Équipe 2", "id": "550e8400-e29b-41d4-a716-446655440003"}
        ])
        
        result = service._getTeamsMapping("550e8400-e29b-41d4-a716-446655440001")
        
        assert result == {
            "Équipe 1": "550e8400-e29b-41d4-a716-446655440002",
            "Équipe 2": "550e8400-e29b-41d4-a716-446655440003"
        }

    def test_get_teams_mapping_exception(self, service, mock_get_supabase):
        """Test de récupération du mapping des équipes avec exception"""
        mock_get_supabase_func, mock_client = mock_get_supabase
        
        # Mock d'exception
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.side_effect = Exception("Database error")
        
        result = service._getTeamsMapping("550e8400-e29b-41d4-a716-446655440001")
        
        assert result == {}

    def test_create_match_with_resolved_teams_success(self, service):
        """Test de création de match avec équipes résolues"""
        match_data = {
            "match_id": "test_1",
            "equipe_a": "Équipe 1",
            "equipe_b": "Équipe 2",
            "terrain": 1,
            "debut_horaire": datetime(2024, 6, 15, 9, 0),
            "fin_horaire": datetime(2024, 6, 15, 9, 15)
        }
        match = Match(**match_data)
        
        teams_mapping = {
            "Équipe 1": "550e8400-e29b-41d4-a716-446655440002",
            "Équipe 2": "550e8400-e29b-41d4-a716-446655440003"
        }
        
        result = service._createMatchWithResolvedTeams(
            planningId="550e8400-e29b-41d4-a716-446655440001",
            match=match,
            phase="round_robin",
            teamsMapping=teams_mapping,
            journee=1
        )
        
        assert result is not None
        assert isinstance(result, AIGeneratedMatch)
        assert result.equipe_a == "Équipe 1"
        assert result.equipe_b == "Équipe 2"
        assert result.resolved_equipe_a_id == "550e8400-e29b-41d4-a716-446655440002"
        assert result.resolved_equipe_b_id == "550e8400-e29b-41d4-a716-446655440003"
        assert result.phase == "round_robin"
        assert result.journee == 1

    def test_create_match_with_resolved_teams_exception(self, service):
        """Test de création de match avec exception"""
        match_data = {
            "match_id": "test_1",
            "equipe_a": "Équipe 1",
            "equipe_b": "Équipe 2",
            "terrain": 1,
            "debut_horaire": datetime(2024, 6, 15, 9, 0),
            "fin_horaire": datetime(2024, 6, 15, 9, 15)
        }
        match = Match(**match_data)
        
        # Mock d'exception dans la création
        with patch('uuid.uuid4', side_effect=Exception("UUID error")):
            result = service._createMatchWithResolvedTeams(
                planningId="550e8400-e29b-41d4-a716-446655440001",
                match=match,
                phase="round_robin",
                teamsMapping={},
                journee=1
            )
            
            assert result is None

    def test_extract_round_robin_matches(self, service, mock_planning_data):
        """Test d'extraction des matchs round robin"""
        ai_planning_data = AIPlanningData(**mock_planning_data)
        teams_mapping = {
            "Équipe 1": "550e8400-e29b-41d4-a716-446655440002",
            "Équipe 2": "550e8400-e29b-41d4-a716-446655440003"
        }
        
        with patch.object(service, '_createMatchWithResolvedTeams') as mock_create:
            mock_create.return_value = Mock(spec=AIGeneratedMatch)
            
            result = service._extractRoundRobinMatches(
                planningId="550e8400-e29b-41d4-a716-446655440001",
                aiPlanningData=ai_planning_data,
                teamsMapping=teams_mapping
            )
            
            assert len(result) == 1
            mock_create.assert_called_once()

    def test_extract_poules_matches(self, service):
        """Test d'extraction des matchs de poules"""
        planning_data = {
            "type_tournoi": "poules_elimination",
            "poules": [
                {
                    "poule_id": "poule_a",
                    "nom_poule": "Poule A",
                    "equipes": ["Équipe 1", "Équipe 2"],
                    "matchs": [
                        {
                            "match_id": "poule_1",
                            "equipe_a": "Équipe 1",
                            "equipe_b": "Équipe 2",
                            "terrain": 1,
                            "debut_horaire": datetime(2024, 6, 15, 9, 0),
                            "fin_horaire": datetime(2024, 6, 15, 9, 15)
                        }
                    ]
                }
            ],
            "commentaires": "Planning avec poules"
        }
        
        ai_planning_data = AIPlanningData(**planning_data)
        teams_mapping = {
            "Équipe 1": "550e8400-e29b-41d4-a716-446655440002",
            "Équipe 2": "550e8400-e29b-41d4-a716-446655440003"
        }
        
        with patch.object(service, '_createMatchWithResolvedTeams') as mock_create:
            mock_create.return_value = Mock(spec=AIGeneratedMatch)
            
            result = service._extractPoulesMatches(
                planningId="550e8400-e29b-41d4-a716-446655440001",
                aiPlanningData=ai_planning_data,
                teamsMapping=teams_mapping
            )
            
            assert len(result) == 1
            mock_create.assert_called_once()

    def test_extract_elimination_matches_no_elimination(self, service, mock_planning_data):
        """Test d'extraction des matchs d'élimination sans phase d'élimination"""
        ai_planning_data = AIPlanningData(**mock_planning_data)
        teams_mapping = {}
        
        result = service._extractEliminationMatches(
            planningId="550e8400-e29b-41d4-a716-446655440001",
            aiPlanningData=ai_planning_data,
            teamsMapping=teams_mapping
        )
        
        assert result == []
