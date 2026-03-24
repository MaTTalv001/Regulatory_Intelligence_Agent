from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_default_region: str = "ap-northeast-1"
    bedrock_model_id: str = "jp.anthropic.claude-sonnet-4-6"
    openfda_api_key: str = ""
    ema_base_url: str = "https://www.ema.europa.eu/en/documents/report"
    ema_epi_base_url: str = "https://epi.ema.europa.eu/consuming/api/fhir"
    openfda_base_url: str = "https://api.fda.gov/drug"
    dailymed_base_url: str = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

    class Config:
        env_file = ".env"


settings = Settings()
