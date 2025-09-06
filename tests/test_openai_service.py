import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.openai_service import OpenAIClientService
import json


class TestOpenAIService:
    """Tests pour le service OpenAI"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock du client OpenAI"""
        with patch('app.services.openai_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_settings(self):
        """Mock des paramètres de configuration"""
        with patch('app.services.openai_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.OPENAI_ASSISTANT_ID = "test-assistant-id"
            yield mock_settings

    @pytest.fixture
    def service(self, mock_openai_client, mock_settings):
        """Service OpenAI avec mocks"""
        return OpenAIClientService()

    def test_init(self, mock_openai_client, mock_settings):
        """Test d'initialisation du service"""
        service = OpenAIClientService()
        assert service.client == mock_openai_client
        assert service.assistant_id == "test-assistant-id"

    def test_generate_planning_success(self, service, mock_openai_client):
        """Test de génération de planning avec succès"""
        # Mock des objets OpenAI
        mock_thread = Mock()
        mock_thread.id = "thread-123"
        mock_openai_client.beta.threads.create.return_value = mock_thread

        mock_run = Mock()
        mock_run.id = "run-123"
        mock_openai_client.beta.threads.runs.create.return_value = mock_run

        # Mock de la réponse complète
        mock_response_text = '{"type_tournoi": "round_robin", "matches": []}'
        
        with patch.object(service, '_wait_for_completion', return_value=mock_response_text):
            with patch.object(service, '_parse_response') as mock_parse:
                mock_parse.return_value = {"type_tournoi": "round_robin", "matches": []}
                
                result = service.generate_planning("Test prompt")
                
                assert result == {"type_tournoi": "round_robin", "matches": []}
                mock_openai_client.beta.threads.create.assert_called_once()
                mock_openai_client.beta.threads.messages.create.assert_called_once_with(
                    thread_id="thread-123",
                    role="user",
                    content="Test prompt"
                )
                mock_openai_client.beta.threads.runs.create.assert_called_once_with(
                    thread_id="thread-123",
                    assistant_id="test-assistant-id"
                )

    def test_generate_planning_exception(self, service, mock_openai_client):
        """Test de génération de planning avec exception"""
        mock_openai_client.beta.threads.create.side_effect = Exception("API Error")
        
        result = service.generate_planning("Test prompt")
        
        assert result is None

    def test_wait_for_completion_success(self, service, mock_openai_client):
        """Test d'attente de completion avec succès"""
        mock_run = Mock()
        mock_run.status = "completed"
        mock_openai_client.beta.threads.runs.retrieve.return_value = mock_run

        mock_message = Mock()
        mock_message.content = [Mock()]
        mock_message.content[0].text.value = '{"type_tournoi": "round_robin"}'
        
        mock_messages = Mock()
        mock_messages.data = [mock_message]
        mock_openai_client.beta.threads.messages.list.return_value = mock_messages

        result = service._wait_for_completion("thread-123", "run-123")
        
        assert result == '{"type_tournoi": "round_robin"}'
        mock_openai_client.beta.threads.runs.retrieve.assert_called_with(
            thread_id="thread-123",
            run_id="run-123"
        )

    def test_wait_for_completion_failed_status(self, service, mock_openai_client):
        """Test d'attente avec statut échoué"""
        mock_run = Mock()
        mock_run.status = "failed"
        mock_openai_client.beta.threads.runs.retrieve.return_value = mock_run

        with pytest.raises(Exception, match="Assistant échoué: failed"):
            service._wait_for_completion("thread-123", "run-123")

    def test_wait_for_completion_no_messages(self, service, mock_openai_client):
        """Test d'attente sans messages de réponse"""
        mock_run = Mock()
        mock_run.status = "completed"
        mock_openai_client.beta.threads.runs.retrieve.return_value = mock_run

        mock_messages = Mock()
        mock_messages.data = []
        mock_openai_client.beta.threads.messages.list.return_value = mock_messages

        with pytest.raises(Exception, match="Aucune réponse de l'assistant"):
            service._wait_for_completion("thread-123", "run-123")

    def test_wait_for_completion_timeout(self, service, mock_openai_client):
        """Test d'attente avec timeout"""
        mock_run = Mock()
        mock_run.status = "running"
        mock_openai_client.beta.threads.runs.retrieve.return_value = mock_run

        with patch('app.services.openai_service.time.sleep'):
            with pytest.raises(Exception, match="Timeout: Assistant trop lent"):
                service._wait_for_completion("thread-123", "run-123")

    def test_parse_response_success(self, service):
        """Test de parsing de réponse avec succès"""
        response_text = '{"type_tournoi": "round_robin", "matches": []}'
        
        result = service._parse_response(response_text)
        
        assert result == {"type_tournoi": "round_robin", "matches": []}

    def test_parse_response_with_markdown(self, service):
        """Test de parsing de réponse avec markdown"""
        response_text = '```json\n{"type_tournoi": "round_robin"}\n```'
        
        result = service._parse_response(response_text)
        
        assert result == {"type_tournoi": "round_robin"}

    def test_parse_response_invalid_json(self, service):
        """Test de parsing de réponse JSON invalide"""
        response_text = '{"type_tournoi": "round_robin", "matches": [}'
        
        with pytest.raises(Exception, match="JSON invalide"):
            service._parse_response(response_text)

    def test_parse_response_not_dict(self, service):
        """Test de parsing de réponse qui n'est pas un dictionnaire"""
        response_text = '["type_tournoi", "round_robin"]'
        
        with pytest.raises(Exception, match="La réponse doit être un objet JSON"):
            service._parse_response(response_text)

    def test_parse_response_missing_type_tournoi(self, service):
        """Test de parsing de réponse sans type_tournoi"""
        response_text = '{"matches": []}'
        
        with pytest.raises(Exception, match="Champ 'type_tournoi' manquant"):
            service._parse_response(response_text)

    def test_parse_response_general_exception(self, service):
        """Test de parsing avec exception générale"""
        response_text = '{"type_tournoi": "round_robin"}'
        
        with patch('json.loads', side_effect=Exception("General error")):
            with pytest.raises(Exception, match="General error"):
                service._parse_response(response_text)

    def test_test_connection_success(self, service, mock_openai_client):
        """Test de connexion avec succès"""
        mock_assistant = Mock()
        mock_assistant.name = "Test Assistant"
        mock_assistant.model = "gpt-4"
        mock_assistant.instructions = "Test instructions" * 20  # Long enough to test truncation
        
        mock_openai_client.beta.assistants.retrieve.return_value = mock_assistant
        
        result = service.test_connection()
        
        assert result is True
        mock_openai_client.beta.assistants.retrieve.assert_called_with("test-assistant-id")

    def test_test_connection_failure(self, service, mock_openai_client):
        """Test de connexion avec échec"""
        mock_openai_client.beta.assistants.retrieve.side_effect = Exception("Connection failed")
        
        result = service.test_connection()
        
        assert result is False
