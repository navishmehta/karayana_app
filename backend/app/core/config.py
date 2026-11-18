"""Environment-dependent settings, read from environment variables / .env.

Where values live:
  - Changes per environment (DB, secrets, URLs)         -> here (.env)
  - Changed by the shop owner at runtime (store name…)  -> app_settings table (enums/setting_key.py)
  - Fixed named options (roles, permissions, codes)      -> app/enums
  - Fixed technical values                               -> core/constants.py
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Smart Kirana API"
    environment: str = "local"  # local | testing | production
    debug: bool = False

    database_url: str = "mysql+pymysql://kirana:password@127.0.0.1:3306/kirana"
    database_echo: bool = False

    # Business defaults
    store_timezone: str = "Asia/Kolkata"
    store_currency: str = "INR"
    default_store_name: str = "Ramesh Karayana Store"  # seed value only; editable later in the admin panel

    # Languages: add "hi" here and a locales/hi.json file to support Hindi.
    supported_locales: list[str] = ["en", "pa"]
    default_locale: str = "en"

    # First admin account, created by the seed command.
    admin_name: str = "Store Admin"
    admin_email: str | None = None
    admin_password: SecretStr | None = None

    # Web catalogue / web admin origins allowed to call the API from a browser.
    cors_origins: list[str] = []

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
