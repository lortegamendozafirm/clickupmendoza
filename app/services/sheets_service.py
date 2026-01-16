"""
Servicio para interactuar con Google Sheets usando ADC (Application Default Credentials).
"""

import logging
from typing import Optional, Dict, Any
import gspread
import google.auth # <--- CAMBIO IMPORTANTE
from google.oauth2.service_account import Credentials # Se mantiene solo para fallback manual
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    Servicio genérico para escribir datos en Google Sheets.
    Usa ADC preferentemente.
    """

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self):
        self.client: Optional[gspread.Client] = None
        self._authenticate()

    def _authenticate(self):
        """
        Autentica con Google Sheets.
        Orden de prioridad:
        1. ADC (Cloud Run Identity / Local gcloud auth) - RECOMENDADO
        2. JSON string (Legacy env var)
        3. File path (Legacy local)
        """
        if not settings.google_sheets_enabled:
            logger.info("Google Sheets integration is disabled")
            return

        try:
            # --- OPCIÓN 1: ADC (Application Default Credentials) ---
            # Esto funciona automáticamente en Cloud Run y en local si usaste 'gcloud auth application-default login'
            logger.info("Attempting authentication via ADC...")
            # google.auth.default() busca credenciales en el entorno automáticamente
            creds, project = google.auth.default(scopes=self.SCOPES)
            self.client = gspread.authorize(creds)
            logger.info(f"Successfully authenticated with Google Sheets via ADC (Project: {project})")
            return

        except Exception as e_adc:
            logger.warning(f"ADC authentication failed, trying legacy methods. Error: {e_adc}")

        # --- FALLBACKS (Código antiguo) ---
        try:
            # Opción 2: JSON string
            credentials_dict = settings.google_credentials_dict
            if credentials_dict:
                logger.info("Authenticating with Google Sheets using JSON credentials")
                creds = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=self.SCOPES
                )
                self.client = gspread.authorize(creds)
                return

            # Opción 3: Path a archivo JSON
            if settings.google_sheets_credentials_path:
                logger.info(f"Authenticating using file: {settings.google_sheets_credentials_path}")
                creds = Credentials.from_service_account_file(
                    settings.google_sheets_credentials_path,
                    scopes=self.SCOPES
                )
                self.client = gspread.authorize(creds)
                return

            logger.error("No valid authentication method found for Google Sheets")

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise

    # ... (El resto de métodos write_row, update_cell, etc. quedan IGUAL) ...
    def write_row(
        self,
        data: Dict[str, Any],
        field_mapping: Optional[Dict[str, int]] = None,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None
    ) -> bool:
        """
        Escribe una fila en Google Sheets de manera dinámica.
        """
        if not settings.google_sheets_enabled:
            return False

        if not self.client:
            logger.error("Google Sheets client not authenticated")
            return False

        try:
            spreadsheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id
            sheet_name = sheet_name or settings.google_sheets_sheet_name
            field_mapping = field_mapping or settings.sheets_field_mapping_dict

            if not spreadsheet_id: return False
            if not field_mapping: return False

            # Abrir spreadsheet y hoja
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)

            max_col = max(field_mapping.values()) if field_mapping else 0
            row_data = [""] * max_col

            for field_name, col_index in field_mapping.items():
                if field_name in data:
                    value = data[field_name]
                    row_data[col_index - 1] = str(value) if value is not None else ""

            worksheet.append_row(row_data, value_input_option='USER_ENTERED')
            logger.info(f"Successfully wrote row to Google Sheets: {spreadsheet_id}/{sheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error writing to Google Sheets: {e}")
            return False