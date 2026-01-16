#app/config.py
"""
Configuración centralizada usando Pydantic Settings.
Lee desde variables de entorno o .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import json


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ClickUp
    clickup_api_token: str
    clickup_webhook_secret: str
    clickup_team_id: Optional[str] = None
    clickup_list_id: Optional[str] = None
    clickup_trigger_condicional: Optional[str] = None
    clickup_field_id_ai_link: str

    # Database
    database_url: Optional[str] = None
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "nexus_legal_db"
    database_user: str = "postgres"
    database_password: str = ""
    database_ssl_mode: str = "require"

    # Google Sheets
    google_sheets_enabled: bool = False
    google_sheets_spreadsheet_id: Optional[str] = None
    google_sheets_sheet_name: str = "Leads DVS"
    google_sheets_credentials_path: Optional[str] = None
    google_sheets_credentials_json: Optional[str] = None
    google_sheets_field_mapping: Optional[str] = None

    # External Dispatch (HTTP POST on webhook trigger)
    external_dispatch_enabled: bool = False
    external_dispatch_url: Optional[str] = None
    filtros_api_key: Optional[str] = None
    external_dispatch_callback_base_url: Optional[str] = None

    # Application
    app_env: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "*"

    # Security
    encryption_key: Optional[str] = None

    @property
    def database_dsn(self) -> str:
        """Construye la URL de conexión a la DB"""
        if self.database_url:
            return self.database_url

        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
            f"?sslmode={self.database_ssl_mode}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte CORS_ORIGINS en lista"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def google_credentials_dict(self) -> Optional[dict]:
        """
        Parsea las credenciales de Google Service Account.
        Prioriza JSON string (para Cloud Run/Secrets) sobre file path.
        """
        if self.google_sheets_credentials_json:
            try:
                return json.loads(self.google_sheets_credentials_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
        return None

    @property
    def sheets_field_mapping_dict(self) -> dict:
        """
        Convierte el mapeo de campos JSON a diccionario.
        Formato esperado: {"task_name": 1, "phone": 2, "email": 3}
        """
        if self.google_sheets_field_mapping:
            try:
                return json.loads(self.google_sheets_field_mapping)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_FIELD_MAPPING: {e}")
        return {}


# Singleton
settings = Settings()
