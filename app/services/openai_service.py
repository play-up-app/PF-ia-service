from openai import OpenAI
from app.core.config import settings
import time
import json

class OpenAIClientService:

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_id = settings.OPENAI_ASSISTANT_ID

    def generate_planning(self, prompt:str) -> dict:
        """
        Génère un planning en appelant ton assistant
        
        Args:
            prompt: Le prompt avec les données du tournoi
            
        Returns:
            dict: Planning généré par l'IA
        """
        try:
            thread = self.client.beta.threads.create()
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            planning_response = self._wait_for_completion(thread.id, run.id)
            
            # 5. Parser la réponse JSON
            planning_data = self._parse_response(planning_response)
            
            print("✅ Planning généré avec succès")
            return planning_data
        except Exception as e:
            print(f"Erreur generation {e}")

    def _wait_for_completion(self, thread_id: str, run_id: str) -> str:
        """Attend que l'assistant termine et récupère la réponse"""
        
        max_wait = 120  # 2 minutes max
        waited = 0
        
        while waited < max_wait:
            # Vérifier le statut
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            print(f"⏳ Statut assistant: {run.status}")
            
            if run.status == "completed":
                # Récupérer la réponse
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.data:
                    return messages.data[0].content[0].text.value
                else:
                    raise Exception("Aucune réponse de l'assistant")
            
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Assistant échoué: {run.status}")
            
            # Attendre un peu
            time.sleep(3)
            waited += 3
        
        raise Exception("Timeout: Assistant trop lent")
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse la réponse texte en JSON"""
        
        try:
            # Nettoyer le texte (enlever markdown si présent)
            clean_text = response_text.strip()
            
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            
            # Parser le JSON
            planning_data = json.loads(clean_text)
            
            # Vérification basique
            if not isinstance(planning_data, dict):
                raise Exception("La réponse doit être un objet JSON")
            
            if "type_tournoi" not in planning_data:
                raise Exception("Champ 'type_tournoi' manquant")
            
            print(f"✅ JSON parsé: {planning_data.get('type_tournoi')}")
            return planning_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            print(f"Réponse reçue: {response_text[:200]}...")
            raise Exception(f"JSON invalide: {e}")
        except Exception as e:
            print(f"❌ Erreur traitement réponse: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            print(f"Assistant trouvé: {assistant.name}")
            print(f"Modèle: {assistant.model}")
            print(f"Instructions: {assistant.instructions[:100]}...")
            
            return True
        except Exception as e:
            print(f"Erreur test connection {e}")
            return False
        
openai_service = OpenAIClientService()