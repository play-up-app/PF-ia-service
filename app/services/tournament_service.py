from typing import List, Optional, Dict, Any
from app.core.database import getSupabase
from app.models.models import Tournament, Team

class TournamentService():
    """
    Service pour gerer les tournois et equipes
    """

    def __init__(self):
        self.supabase = getSupabase()

    def getTournamentById(self, tournamentId: str) -> Optional[Tournament]:
        """
        Récupère un tournoi par son ID
        
        Args:
            tournamentId: ID du tournoi
            
        Returns:
            Tournament: Objet Tournament ou None si pas trouvé
        """
        try:
            print(f"🔍 Récupération tournoi {tournamentId}")
            
            result = self.supabase.table("tournament")\
                .select("*")\
                .eq("id", tournamentId)\
                .single()\
                .execute()
            print(f"result : {result}")
            if not result.data:
                print(f"❌ Tournoi {tournamentId} non trouvé")
                return None
            teams = self.getTournamentTeams(tournamentId)
            result.data["registered_teams"] = len(teams)
                
            # Convertir en objet Pydantic
            tournament = Tournament(**result.data)
            print(f"✅ Tournoi récupéré: {tournament.name}")
            return tournament
            
        except Exception as e:
            print(f"❌ Erreur récupération tournoi {tournamentId}: {e}")
            return None

    def getTournamentTeams(self, tournamentId: str) -> List[Team]:
        """
        Récupère toutes les équipes d'un tournoi
        
        Args:
            tournamentId: ID du tournoi
            
        Returns:
            List[Team]: Liste des équipes (vide si aucune)
        """
        try:
            print(f"👥 Récupération équipes du tournoi {tournamentId}")
            
            result = self.supabase.table("team")\
                .select("*")\
                .eq("tournament_id", tournamentId)\
                .order("name")\
                .execute()
            
            teams = []
            for team_data in result.data or []:
                try:
                    team = Team(**team_data)
                    teams.append(team)
                except Exception as e:
                    print(f"⚠️ Équipe invalide ignorée: {e}")
                    continue
            
            print(f"✅ {len(teams)} équipes récupérées")
            return teams
            
        except Exception as e:
            print(f"❌ Erreur récupération équipes: {e}")
            return []

    def getTournamentWithTeams(self, tournamentId: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un tournoi avec ses équipes
        
        Args:
            tournmentId: ID du tournoi
            
        Returns:
            dict: {"tournament": Tournament, "teams": List[Team]} ou None si erreur
        """
        try:
            print(f"🔍 Récupération tournoi + équipes {tournamentId}")
            
            tournament = self.getTournamentById(tournamentId)
            if not tournament:
                return None
            teams = self.getTournamentTeams(tournamentId)
            if len(teams) < 1:
                return None
            result = {
                "tournament": tournament,
                "teams": teams,
                "teams_count": len(teams),
                "has_minimum_teams": len(teams) >= 2,
                "can_start": len(teams) >= 2 and tournament.status == "ready"
            }
            
            print(f"✅ Tournoi + {len(teams)} équipes récupérés")
            return result
            
        except Exception as e:
            print(f"❌ Erreur récupération tournoi avec équipes: {e}")
            return None

    def _validateTournamentData(self, tournamentData: Dict[str, Any]) -> bool:
        """Valide si le tournoi peut avoir un planning généré"""
        try:
            tournament = tournamentData["tournament"]
            teams = tournamentData["teams"]
            
            print(f"🔍 Validation: {len(teams)} équipes, {tournament.courts_available} terrains")
            
            # Vérifier nombre minimum d'équipes
            if len(teams) < 2:
                print("❌ Pas assez d'équipes (minimum 2)")
                return False
            
            # Vérifier nombre maximum d'équipes
            if len(teams) > tournament.max_teams:
                print(f"❌ Trop d'équipes ({len(teams)} > {tournament.max_teams})")
                return False
            
            # Vérifier terrains
            if tournament.courts_available <= 0:
                print("❌ Nombre de terrains invalide")
                return False
            
            # Vérifier type de tournoi
            if not tournament.tournament_type:
                print("❌ Type de tournoi manquant")
                return False
            
            print("✅ Validation réussie")
            return True
            
        except Exception as e:
            print(f"❌ Erreur validation: {e}")
            return False

tournamentService = TournamentService()