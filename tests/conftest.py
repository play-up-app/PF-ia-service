import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, time
from typing import Dict, Any, List

# Mock des modèles
@pytest.fixture
def mock_tournament_data():
    """Données mockées pour un tournoi"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Tournoi Test",
        "description": "Tournoi de test",
        "tournament_type": "round_robin",
        "max_teams": 8,
        "registered_teams": 4,
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
def mock_team_data():
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

@pytest.fixture
def mock_planning_data():
    """Données mockées pour un planning IA"""
    return {
        "type_tournoi": "round_robin",
        "matchs_round_robin": [
            {
                "match_id": "rr_1",
                "equipe_a": "Équipe 1",
                "equipe_b": "Équipe 2",
                "debut_horaire": datetime(2024, 6, 15, 9, 0),
                "fin_horaire": datetime(2024, 6, 15, 9, 15),
                "terrain": 1,
                "journee": 1
            }
        ],
        "poules": [],
        "phase_elimination_apres_poules": None,
        "rounds_elimination": {},
        "winner_bracket": {},
        "loser_bracket": {},
        "grande_finale": {},
        "final_ranking": [],
        "commentaires": "Planning généré avec succès"
    }

@pytest.fixture
def mock_supabase_client():
    """Mock du client Supabase"""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    return mock_client, mock_table

@pytest.fixture
def mock_openai_client():
    """Mock du client OpenAI"""
    mock_client = Mock()
    mock_beta = Mock()
    mock_threads = Mock()
    mock_assistants = Mock()
    
    mock_client.beta = mock_beta
    mock_beta.threads = mock_threads
    mock_beta.assistants = mock_assistants
    
    return mock_client, mock_threads, mock_assistants

@pytest.fixture
def mock_settings():
    """Mock des paramètres de configuration"""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.OPENAI_ASSISTANT_ID = "test-assistant-id"
        mock_settings.SUPABASE_URL = "https://test.supabase.co"
        mock_settings.SUPABASE_KEY = "test-key"
        mock_settings.SUPABASE_SERVICE_KEY = "test-service-key"
        yield mock_settings

@pytest.fixture
def mock_get_supabase():
    """Mock de la fonction getSupabase avec configuration améliorée"""
    with patch('app.core.database.getSupabase') as mock_get_supabase:
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        # Configuration par défaut du mock table
        mock_select = Mock()
        mock_eq = Mock()
        mock_single = Mock()
        mock_execute = Mock()
        mock_order = Mock()
        
        # Configuration de la chaîne de mocks
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = mock_execute
        mock_eq.order.return_value = mock_order
        mock_order.execute.return_value = mock_execute
        
        # Configuration par défaut pour retourner des données vides
        mock_execute.data = []
        
        mock_get_supabase.return_value = mock_client
        yield mock_get_supabase, mock_client, mock_table

@pytest.fixture
def mock_ai_planning_service(mock_get_supabase):
    """Mock du service AIPlanningService"""
    with patch('app.services.ai_planning_service.AIPlanningService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.generatePlanning = Mock()
        mock_instance.getPlanningStatus = Mock()
        mock_instance.regeneratePlanning = Mock()
        mock_instance._buildStaticPrompt = Mock()
        mock_instance._deletePlanning = Mock()
        mock_instance._getPlanningById = Mock()
        mock_instance._deletePlanningByTournamentId = Mock()
        yield mock_instance
