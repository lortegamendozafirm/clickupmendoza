"""
Servicio para interactuar con Google Sheets usando Service Account.
Soporta autenticación desde JSON string o file path.
"""

import logging
from typing import Optional, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Servicio genérico para escribir datos en Google Sheets.
    Usa Service Account para autenticación.
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
        Autentica con Google Sheets API usando Service Account.
        Prioriza credenciales JSON (para Cloud Run) sobre file path.
        """
        if not settings.google_sheets_enabled:
            logger.info("Google Sheets integration is disabled")
            return

        try:
            # Opción 1: JSON string desde variable de entorno (Cloud Run/Secrets)
            credentials_dict = settings.google_credentials_dict
            if credentials_dict:
                logger.info("Authenticating with Google Sheets using JSON credentials")
                creds = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=self.SCOPES
                )
                self.client = gspread.authorize(creds)
                logger.info("Successfully authenticated with Google Sheets (JSON)")
                return

            # Opción 2: Path a archivo JSON (desarrollo local)
            if settings.google_sheets_credentials_path:
                logger.info(f"Authenticating with Google Sheets using file: {settings.google_sheets_credentials_path}")
                creds = Credentials.from_service_account_file(
                    settings.google_sheets_credentials_path,
                    scopes=self.SCOPES
                )
                self.client = gspread.authorize(creds)
                logger.info("Successfully authenticated with Google Sheets (file)")
                return

            logger.warning("Google Sheets enabled but no credentials provided")

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise

    def write_row(
        self,
        data: Dict[str, Any],
        field_mapping: Optional[Dict[str, int]] = None,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None
    ) -> bool:
        """
        Escribe una fila en Google Sheets de manera dinámica.

        Args:
            data: Diccionario con los datos a escribir.
                  Ejemplo: {"task_name": "Juan Perez", "phone": "555-1234", "email": "juan@example.com"}
            field_mapping: Mapeo de campos a columnas (1-indexed).
                          Ejemplo: {"task_name": 1, "phone": 2, "email": 3}
                          Si es None, usa el mapping de settings.
            spreadsheet_id: ID del spreadsheet. Si es None, usa el de settings.
            sheet_name: Nombre de la hoja. Si es None, usa el de settings.

        Returns:
            True si la escritura fue exitosa, False en caso contrario.
        """
        if not settings.google_sheets_enabled:
            logger.debug("Google Sheets is disabled, skipping write_row")
            return False

        if not self.client:
            logger.error("Google Sheets client not authenticated")
            return False

        try:
            # Usar valores por defecto de settings si no se especifican
            spreadsheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id
            sheet_name = sheet_name or settings.google_sheets_sheet_name
            field_mapping = field_mapping or settings.sheets_field_mapping_dict

            if not spreadsheet_id:
                logger.error("No spreadsheet ID provided")
                return False

            if not field_mapping:
                logger.warning("No field mapping provided, cannot write row")
                return False

            # Abrir spreadsheet y hoja
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)

            # Construir la fila según el mapeo
            # Encontrar el índice de columna máximo para inicializar la fila
            max_col = max(field_mapping.values()) if field_mapping else 0
            row_data = [""] * max_col

            # Llenar los datos según el mapeo
            for field_name, col_index in field_mapping.items():
                if field_name in data:
                    value = data[field_name]
                    # Convertir a string si no lo es
                    row_data[col_index - 1] = str(value) if value is not None else ""

            # Agregar la fila al final del sheet
            worksheet.append_row(row_data, value_input_option='USER_ENTERED')

            logger.info(f"Successfully wrote row to Google Sheets: {spreadsheet_id}/{sheet_name}")
            return True

        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet '{sheet_name}' not found in spreadsheet {spreadsheet_id}")
            return False
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet {spreadsheet_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error writing to Google Sheets: {e}")
            return False

    def update_cell(
        self,
        row: int,
        col: int,
        value: Any,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None
    ) -> bool:
        """
        Actualiza una celda específica en Google Sheets.

        Args:
            row: Número de fila (1-indexed)
            col: Número de columna (1-indexed)
            value: Valor a escribir
            spreadsheet_id: ID del spreadsheet
            sheet_name: Nombre de la hoja

        Returns:
            True si la actualización fue exitosa, False en caso contrario.
        """
        if not settings.google_sheets_enabled or not self.client:
            return False

        try:
            spreadsheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id
            sheet_name = sheet_name or settings.google_sheets_sheet_name

            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update_cell(row, col, value)

            logger.info(f"Successfully updated cell ({row}, {col}) in {sheet_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating cell in Google Sheets: {e}")
            return False

    def get_all_records(
        self,
        spreadsheet_id: Optional[str] = None,
        sheet_name: Optional[str] = None
    ) -> list:
        """
        Obtiene todos los registros de una hoja como lista de diccionarios.

        Args:
            spreadsheet_id: ID del spreadsheet
            sheet_name: Nombre de la hoja

        Returns:
            Lista de diccionarios con los datos de la hoja
        """
        if not settings.google_sheets_enabled or not self.client:
            return []

        try:
            spreadsheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id
            sheet_name = sheet_name or settings.google_sheets_sheet_name

            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records()

            logger.info(f"Retrieved {len(records)} records from {sheet_name}")
            return records

        except Exception as e:
            logger.error(f"Error getting records from Google Sheets: {e}")
            return []
