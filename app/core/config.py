from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Classe pour récupérer les variables d'environnement"""
    # SUPABASE
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str # cle admin
    SUPABASE_KEY: str

    # OPENAI
    OPENAI_API_KEY: str
    OPENAI_ASSISTANT_ID: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8")
    
@lru_cache()
def get_settings() -> Settings:
    """
    Function to get the application settings.
    """
    return Settings()

# Instance globale
settings = Settings()
