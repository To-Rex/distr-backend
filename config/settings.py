from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class AppSettings(BaseSettings):
    DEBUG: bool = Field(default=False)

    LOCAL_DOMAIN: str = Field(default="http://127.0.0.1:8000")
    GLOBAL_DOMAIN: str = Field(default="https://distr.mxsoft.uz")

    @computed_field
    @property
    def BASE_URL(self) -> str:
        """Automatically switches domain based on DEBUG mode."""
        return self.LOCAL_DOMAIN if self.DEBUG else self.GLOBAL_DOMAIN

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = AppSettings()
