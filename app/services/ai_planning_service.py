from typing import Any, Dict, Optional

from app.core.database import getSupabase
from app.models.models import AITournamentPlanning
from app.services.database_service import databaseService
from app.services.openai_service import openai_service
from app.services.tournament_service import tournamentService


class AIPlanningService:
    def __init__(self):
        self.supabase = getSupabase()
        self.openAIService = openai_service
        self.databaseService = databaseService
        self.tournamentService = tournamentService

    def generatePlanning(self, tournamentId: str) -> Optional[AITournamentPlanning]:
        """
        Génère un planning complet pour un tournoi

        Args:
            tournament_id: ID du tournoi

        Returns:
            AITournamentPlanning si succès, None sinon
        """
        try:
            # Récupération des données tournoi avec équipes
            tournamentData = self.tournamentService.getTournamentWithTeams(tournamentId)
            if not tournamentData:
                print("Impossible de récupérer les données du tournoi")
                return None

            # valide les donnees
            isValidTournamentData = self.tournamentService._validateTournamentData(
                tournamentData
            )
            if not isValidTournamentData:
                print("Tournament data non valide")
                return None

            # construction prompt
            prompt = self._buildStaticPrompt(tournamentData)

            # appel OpenAI
            aiResponse = self.openAIService.generate_planning(prompt)
            if not aiResponse:
                print("Echec OpenAI")
                return None

            # sauvegarde via database service
            tournament = tournamentData["tournament"]
            planning = self.databaseService.savePlanning(
                tournamentId, aiResponse, tournament.tournament_type
            )

            if not planning:
                print("Echec sauvegarde planning")
                return None

            # sauvegarde les matchs
            matches = self.databaseService.saveMatches(planning.id, aiResponse)
            if matches is None:
                print("Echec sauvegarde matchs - suppression planning")
                self._deletePlanning(planning.id)
                return None

            # sauvegarde les poules
            poules = self.databaseService.savePoules(planning.id, aiResponse)
            if poules is None:
                print("Echec sauvegarde poules - suppression planning")
                self._deletePlanning(planning.id)
                return None

            print(f"Planning genere : {planning.id}")

            return planning
        except Exception as e:
            print(f"Erreur generation planning: {e}")
            return None

    def getPlanningStatus(self, planningId: str) -> Optional[str]:
        """
        Récupère le statut d'un planning

        Args:
            planning_id: ID du planning

        Returns:
            Statut du planning ou None si erreur
        """
        try:
            print(f"🔍 Vérification statut planning {planningId}")

            result = (
                self.supabase.table("ai_tournament_planning")
                .select("status")
                .eq("id", planningId)
                .execute()
            )

            if not result.data:
                print("❌ Planning non trouvé")
                return None

            status = result.data[0]["status"]
            print(f"✅ Statut: {status}")
            return status

        except Exception as e:
            print(f"❌ Erreur récupération statut: {e}")
            return None

    def regeneratePlanning(self, planningId: str) -> Optional[AITournamentPlanning]:
        """
        Régénère un planning existant

        Args:
            planning_id: ID du planning à régénérer

        Returns:
            Nouveau planning généré ou None si erreur
        """
        try:
            print(f"🔄 Régénération planning {planningId}")

            # Récupérer l'ancien planning pour obtenir le tournament_id
            old_planning = self._getPlanningById(planningId)
            if not old_planning:
                print("❌ Planning original non trouvé")
                return None

            # Supprimer l'ancien planning
            self._deletePlanning(planningId)

            # Générer un nouveau planning
            new_planning = self.generatePlanning(old_planning.tournament_id)

            if new_planning:
                print(f"✅ Planning régénéré: {new_planning.id}")

            return new_planning

        except Exception as e:
            print(f"❌ Erreur régénération planning: {e}")
            return None

    def _buildStaticPrompt(self, tournamentData: Dict[str, Any]) -> str:
        """Construit le prompt statique pour l'IA"""
        tournament = tournamentData["tournament"]
        teams = tournamentData["teams"]

        team_names = [team.name for team in teams]

        # Prompt statique optimisé
        prompt = f"""
            Tu es un expert en organisation de tournois de volley-ball. 
            Génère un planning complet au format JSON pour ce tournoi :

            INFORMATIONS TOURNOI:
            - Nom: {tournament.name}
            - Type: {tournament.tournament_type}
            - Nombre max d'équipes: {len(teams)}
            - Équipes: {', '.join(team_names)}
            - Terrains disponibles: {tournament.courts_available}
            - Date de début: {tournament.start_date}
            - Heure de début: {tournament.start_time or '09:00'}
            - Durée match: {tournament.match_duration_minutes} minutes
            - Pause entre matchs: {tournament.break_duration_minutes} minutes

            CONTRAINTES OBLIGATOIRES - TRÈS IMPORTANT:
            GESTION DES TERRAINS: Sur un même terrain, deux matchs consécutifs DOIVENT avoir un intervalle 
            minimum de {tournament.break_duration_minutes} minutes entre la fin du premier match et le début 
            du suivant.

            CALCUL DES HORAIRES: 
            - Si un match se termine à 09h20 sur le terrain 1
            - Et que la pause configurée est de 5 minutes
            - Le prochain match sur le terrain 1 ne peut commencer AVANT 09h25

            EXEMPLE DE RESPECT DES CONTRAINTES:
            Terrain 1: Match 1 (09h00-09h15) → Pause 5min → Match 2 (09h20-09h35)
            Terrain 2: Match 3 (09h00-09h15) → Pause 5min → Match 4 (09h20-09h35)

            CONTRAINTES SUPPLEMENTAIRES:
            - Tous les matchs doivent rentrer dans la journée
            - Optimiser l'utilisation des terrains
            - Éviter les temps d'attente trop longs

            CONTRAINTES OBLIGATOIRES:
            - Pas de match entre 12h et 13h30.
            - Tu utilises tous les terrains disponibles pour la plannification des matchs.

            IMPORTANT: Réponds UNIQUEMENT avec du JSON valide selon le type de tournoi.
            Pour round_robin: utilise la structure avec matchs_round_robin.
            Pour elimination_directe: utilise la structure avec rounds_elimination.
            Pour poules_elimination: utilise la structure avec poules et phase_elimination_apres_poules.

            Le JSON doit inclure obligatoirement le champ "type_tournoi" avec la valeur "{tournament.tournament_type}".
            """

        print("✅ Prompt statique construit")
        return prompt

    def _deletePlanning(self, planningId: str) -> bool:
        """Supprime un planning et ses détails"""
        try:
            # Supprimer d'abord les détails (tables liées)
            self.supabase.table("ai_generated_match").delete().eq(
                "planning_id", planningId
            ).execute()
            self.supabase.table("ai_generated_poule").delete().eq(
                "planning_id", planningId
            ).execute()

            # Supprimer le planning principal
            result = (
                self.supabase.table("ai_tournament_planning")
                .delete()
                .eq("id", planningId)
                .execute()
            )

            print(f"🗑️ Planning {planningId} supprimé")
            return True

        except Exception as e:
            print(f"❌ Erreur suppression planning: {e}")
            return False

    def _getPlanningById(self, planningId: str) -> Optional[AITournamentPlanning]:
        """Récupère un planning par son ID"""
        try:
            result = (
                self.supabase.table("ai_tournament_planning")
                .select("*")
                .eq("id", planningId)
                .execute()
            )

            if not result.data:
                return None

            return AITournamentPlanning(**result.data[0])

        except Exception as e:
            print(f"❌ Erreur récupération planning: {e}")
            return None

    def _deletePlanningByTournamentId(self, tournamentId: str) -> bool:
        """Supprime tous les plannings d'un tournoi"""
        try:
            # transaction pour supprimer les plannings et les matchs et les poules
            self.supabase.transaction(
                lambda tx: tx.table("ai_tournament_planning")
                .delete()
                .eq("tournament_id", tournamentId)
                .execute()
            )
            self.supabase.transaction(
                lambda tx: tx.table("ai_generated_match")
                .delete()
                .eq("planning_id", tournamentId)
                .execute()
            )
            self.supabase.transaction(
                lambda tx: tx.table("ai_generated_poule")
                .delete()
                .eq("planning_id", tournamentId)
                .execute()
            )

            return True
        except Exception as e:
            print(f"❌ Erreur suppression planning: {e}")
            return False


aiPlanningService = AIPlanningService()
