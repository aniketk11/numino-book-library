from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://library:library@db:5432/library"
    loan_period_days: int = 14
    daily_fine_rate: float = 20  # INR per day overdue

    class Config:
        env_file = ".env"


settings = Settings()
