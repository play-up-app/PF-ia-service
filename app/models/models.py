from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time 

class Tournament(BaseModel):
    """Représente un tournoi"""
    
    id: str
    name: str
    description: Optional[str]
    tournament_type: str  # 'round_robin', 'elimination_directe', etc.
    max_teams: int
    registered_teams: int = 0
    courts_available: int
    start_date: date
    start_time: Optional[time] = None
    match_duration_minutes: int = 15
    break_duration_minutes: int = 5
    constraints: Dict[str, Any] = {}  # JSON avec pause déjeuner, etc.
    organizer_id: str
    status: str = 'draft'
    created_at: datetime
    updated_at: datetime

class Team(BaseModel):
    """Représente une équipe"""
    
    id: str
    name: str
    description: str
    tournament_id: str
    captain_id: Optional[str] = None
    status: str = 'registered'
    contact_email: str
    contact_phone: str
    skill_level: str
    notes: str
    created_at: datetime
    updated_at: datetime

class TeamMember(BaseModel):
    """Représente un membre d'une équipe"""
    id: str
    team_id: str
    user_id: str
    email: str
    role: str = 'player' 
    position: Optional[str] = None  # Position peut être None
    status: str
    joined_at: datetime
    created_at: datetime

class TeamWithMembers(Team):
    """Représente une équipe avec ses membres"""
    members: List[TeamMember] = []

class Match(BaseModel):
    """Représente un match de base"""
    
    match_id: str
    equipe_a: str
    equipe_b: str
    debut_horaire: datetime
    fin_horaire: datetime
    terrain: int

class RoundRobinMatch(Match):
    """Match de round robin"""
    journee: Optional[int] = None

class PouleMatch(Match):
    """Match de poule"""
    pass

class EliminationMatch(Match):
    """Match d'élimination"""
    pass

class Poule(BaseModel):
    """Représente une poule"""
    
    poule_id: str
    nom_poule: str
    equipes: List[str]
    matchs: List[PouleMatch] = []

class EliminationPhase(BaseModel):
    """Phase d'élimination après poules"""
    
    quarts: List[EliminationMatch] = []
    demi_finales: List[EliminationMatch] = []
    finale: Optional[EliminationMatch] = None
    match_troisieme_place: Optional[EliminationMatch] = None

class FinalRanking(BaseModel):
    """Classement final"""
    
    position: int
    equipe_id: str
    nom_equipe: Optional[str] = None

class AIPlanningData(BaseModel):
    """Données complètes d'un planning généré par l'IA"""
    
    type_tournoi: str
    
    # Round Robin
    matchs_round_robin: List[RoundRobinMatch] = []
    
    # Poules + Elimination
    poules: List[Poule] = []
    phase_elimination_apres_poules: Optional[EliminationPhase] = None
    
    # Autres types (à développer plus tard)
    rounds_elimination: Dict[str, Any] = {}
    winner_bracket: Dict[str, Any] = {}
    loser_bracket: Dict[str, Any] = {}
    grande_finale: Dict[str, Any] = {}
    
    # Commun
    final_ranking: List[FinalRanking] = []
    commentaires: Optional[str] = None
    
    def calculate_total_matches(self) -> int:
        """Calcule le nombre total de matchs"""
        total = 0
        
        # Round robin
        total += len(self.matchs_round_robin)
        
        # Matchs dans les poules
        for poule in self.poules:
            total += len(poule.matchs)
        
        # Phase d'élimination après poules
        if self.phase_elimination_apres_poules:
            total += len(self.phase_elimination_apres_poules.quarts)
            total += len(self.phase_elimination_apres_poules.demi_finales)
            if self.phase_elimination_apres_poules.finale:
                total += 1
            if self.phase_elimination_apres_poules.match_troisieme_place:
                total += 1
        
        return total

class AITournamentPlanning(BaseModel):
    """Planning généré par l'IA (table principale)"""
    
    id: Optional[str] = None
    tournament_id: str
    type_tournoi: str
    status: str = 'generating'
    planning_data: Dict[str, Any] = {}  # JSON complet de l'IA
    total_matches: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    ai_comments: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_planning_data_object(self) -> Optional[AIPlanningData]:
        """Retourne les données de planning comme objet AIPlanningData"""
        if self.planning_data:
            return AIPlanningData(**self.planning_data)
        return None

class AIGeneratedMatch(BaseModel):
    """Match généré par l'IA"""
    
    id: Optional[str] = None
    planning_id: str
    match_id_ai: str  # 'poule_a_m1', 'elim_quart_1'
    equipe_a: str  # 'Équipe 1' ou 'winner_quart_1'
    equipe_b: str
    terrain: int
    debut_horaire: datetime
    fin_horaire: datetime
    phase: str  # 'poules', 'elimination', 'finale'
    poule_id: Optional[str] = None  # Si c'est un match de poule
    journee: Optional[int] = None  # Si c'est du round robin
    status: str = 'scheduled'
    resolved_equipe_a_id: Optional[str] = None
    resolved_equipe_b_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def is_placeholder(self) -> bool:
        """Vérifie si le match contient des placeholders"""
        placeholders = ['winner_', 'loser_', '1er_', '2e_']
        return any(ph in self.equipe_a for ph in placeholders) or any(ph in self.equipe_b for ph in placeholders)

class AIGeneratedPoule(BaseModel):
    """Poule générée par l'IA"""
    
    id: Optional[str] = None
    planning_id: str
    poule_id: str  # 'poule_a'
    nom_poule: str  # 'Poule A'
    equipes: List[str] = []  # Liste des noms d'équipes
    nb_equipes: int = 0
    nb_matches: int = 0
    created_at: Optional[datetime] = None

class Profile(BaseModel):
    """Représente un profil utilisateur (table profile publique)"""
    
    id: str  # UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: bool = True
    push_notifications: bool = True
    is_active: bool = True
    email_verified: bool = False
    metadata: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

User = Profile