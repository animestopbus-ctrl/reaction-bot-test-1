import os
from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str
    DATABASE_NAME: str = "telegram_reaction_saas"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Telegram
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_SESSION_NAME: str = "telegram_reaction_bot"
    LOG_CHANNEL_ID: int = 0
    
    # Owner
    OWNER_TELEGRAM_ID: int
    OWNER_USERNAME: str = "admin"
    OWNER_PASSWORD: str
    
    # Application
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000"
    API_PREFIX: str = "/api/v1"
    PORT: int = 8000
    
    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Background API
    WALLPAPER_API_PRIMARY: str = "https://nekos.best/api/v2/wallpaper"
    WALLPAPER_API_FALLBACK: str = "https://api.waifu.pics/sfw/waifu"
    WALLPAPER_CACHE_TTL: int = 3600
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
