from supabase import create_client, Client
from typing import Optional
from app.core.config import settings 

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY  
SUPABASE_SERVICE_KEY = settings.SUPABASE_SERVICE_KEY 

supabase: Optional[Client] = None

def initSupabase():
    global supabase

    if SUPABASE_URL is None:
        raise Exception("SUPABASE_URL manquant dans les variables d'environnement")
    if SUPABASE_KEY is None:
        raise Exception("SUPABASE_KEY manquant dans les variables d'environnement")
    
    if SUPABASE_SERVICE_KEY is None:
        raise Exception("SUPABASE_SERVICE_KEY manquant dans les variables d'environnement")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        print("Connexion à Supabase !")
    except Exception as e:
        print(f"Erreur : {e}")
        raise

def getSupabase():
    initSupabase()
    if supabase is None:
        raise Exception("Supabase pas initialisé - appeler init_supabase() d'abord")
    
    return supabase

def testConnection():
    try:
        db = getSupabase()
        
        # Test simple - récupérer les tournois (même s'il n'y en a pas)
        result = db.table("tournaments").select("id").limit(1).execute()
        
        print("✅ Test connexion DB réussi")
        print(f"Données récupérées: {len(result.data)} lignes")
        return True
        
    except Exception as e:
        print(f"❌ Test connexion échoué: {e}")
        return False
