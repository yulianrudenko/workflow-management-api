from pydantic_settings import BaseSettings

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

class Settings(BaseSettings):
    SECRET_KEY: str
    DB_URL: str
    TESTS_DB_URL: str

settings = Settings()
