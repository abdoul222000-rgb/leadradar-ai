import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LEADRADAR_APP_NAME: str = "LeadRadar AI"
    APP_SLOGAN: str = "The #1 Zero-Ad Reddit & X Lead Engine for Founders"
    SECRET_KEY: str = "leadradar-super-secret-key-2026-high-conversion-suite"
    LEADRADAR_DATABASE_URL: str = "sqlite:///./leadradar.db"

    @property
    def APP_NAME(self) -> str:
        return self.LEADRADAR_APP_NAME

    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("LEADRADAR_DATABASE_URL", "sqlite:///./leadradar.db")
    
    # Port d'écoute
    PORT: int = int(os.getenv("PORT", 8070))
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8070")

    # Identifiants Maître Fondateur / SuperAdmin (Accès Diabagate Assouman)
    FOUNDER_NAME: str = "Diabagate Assouman abdoul Aziz"
    FOUNDER_EMAIL: str = "abdoul222000@gmail.com"
    FOUNDER_PIN: str = "4568"
    FOUNDER_PASSWORD: str = "@Abdoul20017"
    
    # Intelligence Artificielle (Optionnel: OpenAI API Key si disponible)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str = "gpt-4o-mini"
    
    # Lemon Squeezy Configuration (Paiements Automatiques)
    LEMON_SQUEEZY_STORE_ID: str = os.getenv("LEMON_SQUEEZY_STORE_ID", "lemon_store_leadradar_2026")
    LEMON_SQUEEZY_API_KEY: str = os.getenv("LEMON_SQUEEZY_API_KEY", "")
    LEMON_SQUEEZY_WEBHOOK_SECRET: str = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec_leadradar_secret_2026")
    
    # Liens de Checkout Lemon Squeezy (Plans $29 Starter & $69 Growth)
    LEMON_SQUEEZY_STARTER_URL: str = os.getenv(
        "LEMON_SQUEEZY_STARTER_URL", 
        "https://leadradar.lemonsqueezy.com/buy/starter-monthly"
    )
    LEMON_SQUEEZY_GROWTH_URL: str = os.getenv(
        "LEMON_SQUEEZY_GROWTH_URL", 
        "https://leadradar.lemonsqueezy.com/buy/growth-monthly"
    )
    
    # Coordonnées Bancaires Officielles Grey USD (Lead Bank) pour encaissement des Payouts
    LEAD_BANK_NAME: str = "Lead Bank"
    LEAD_BANK_BENEFICIARY_NAME: str = "Diabagate Assouman abdoul Aziz"
    LEAD_BANK_ACCOUNT_NUMBER: str = "213069059479"
    LEAD_BANK_ACCOUNT_TYPE: str = "Checking"
    LEAD_BANK_ROUTING: str = "101019644"
    LEAD_BANK_ACCOUNT_LAST4: str = "9479"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
