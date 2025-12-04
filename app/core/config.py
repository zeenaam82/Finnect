from pydantic_settings import BaseSettings
import os

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

    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY")
    BUCKET_NAME: str = os.getenv("BUCKET_NAME")
    REGION: str = os.getenv("REGION", "ap-northeast-2")
    
    # S3 폴더 구조
    S3_RAW_FOLDER: str = os.getenv('RAW_FOLDER')
    S3_PROCESSED_FOLDER: str = os.getenv('PROCESSED_FOLDER')
    S3_RAW_DATASET_FOLDER: str = os.getenv('RAW_DATASET_FOLDER')
    S3_TRAINING_DATA_FOLDER: str = os.getenv('TRAINING_DATA_FOLDER')
    # S3_IMAGE_FOLDER = "images"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
