from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Finnect"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    S3_BUCKET: str = ""
    AWS_REGION: str = ""
    ONNX_MODEL_S3_KEY: str = ""
    OPENAI_API_KEY: str

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    django_secret_key: str
    django_debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
