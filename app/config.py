import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SECRET: str = "my_secret_key"
    ALLOWED_REPOS: List[str] = []

    DOCKER_IMAGE: str = "grader-image:latest"
    CPU_LIMIT: str = "1"      # docker --cpus
    MEM_LIMIT: str = "512m"    # docker --memory
    TIMEOUT_SEC: int = 100

    if not SECRET or not ALLOWED_REPOS:
        raise ValueError("SECRET KEY and ALLOWED REPOSITORIES are NEEDED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()