from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    SECRET_KEY: str = "12345678"
    DEVELOPMENT: bool = True

    PG_DRIVER: str = "postgresql+psycopg"
    PG_USERNAME: str
    PG_PASSWORD: str
    PG_HOST: str = "10.0.10.13"
    PG_PORT: int = 5432
    PG_DATABASE: str = "test"

    secret_dp_S3_ACCOUNT_ID : str
    secret_dp_S3_ACCESS_KEY : str
    secret_dp_S3_SECRET : str

    main_BUCKET_NAME :str

    @computed_field
    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            self.PG_DRIVER,
            username=self.PG_USERNAME,
            password=self.PG_PASSWORD,
            host=self.PG_HOST,
            port=self.PG_PORT,
            database=self.PG_DATABASE
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore")


settings = Settings()
