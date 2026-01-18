from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RuptrAPI"
    # Postgres running in conda env on unix socket /tmp
    DATABASE_URL: str = "postgresql://arjungovindan:@/ruptrapi?host=/tmp"
    
    @property
    def ASYNC_DATABASE_URL(self):
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
