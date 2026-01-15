from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RuptrAPI"
    # Postgres running in conda env on unix socket /tmp
    DATABASE_URL: str = "postgresql://arjungovindan:@/ruptrapi?host=/tmp"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
