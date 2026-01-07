"""
Utilidades para normalización de texto.
Replica la lógica de R para nombres, teléfonos, fechas.
"""

import re
from unidecode import unidecode
from typing import Optional


def normalize_name(text: str) -> str:
    """
    Normaliza un nombre para búsqueda fuzzy.

    Pasos (equivalente a R):
    1. Convertir a ASCII (quitar tildes: López -> Lopez)
    2. Mayúsculas
    3. Eliminar caracteres no alfanuméricos (dejar solo A-Z, 0-9, espacios)
    4. Squish: reducir espacios múltiples a uno solo y trim

    Args:
        text: Nombre original

    Returns:
        Nombre normalizado
    """
    if not text:
        return ""

    # 1. ASCII (remover acentos)
    ascii_text = unidecode(text)

    # 2. Mayúsculas
    upper_text = ascii_text.upper()

    # 3. Solo A-Z, 0-9, espacios
    clean_text = re.sub(r"[^A-Z0-9 ]", "", upper_text)

    # 4. Squish: múltiples espacios -> uno solo, y trim
    normalized = re.sub(r"\s+", " ", clean_text).strip()

    return normalized


def clean_phone(phone: Optional[str]) -> Optional[str]:
    """
    Limpia un teléfono dejando solo dígitos.
    Valida longitud (10-15 dígitos).

    Args:
        phone: Teléfono raw

    Returns:
        Solo dígitos si válido, None si inválido
    """
    if not phone:
        return None

    # Eliminar todo excepto números
    digits = re.sub(r"[^0-9]", "", phone)

    # Validar longitud
    if 10 <= len(digits) <= 15:
        return digits

    return None


def remove_ordinal_suffix(date_text: str) -> str:
    """
    Elimina sufijos ordinales de fechas en inglés (1st, 2nd, 3rd, 4th).
    Ejemplo: "May 21st 2024" -> "May 21 2024"

    Usa Lookbehind: (?<=\\d) = "solo si hay un dígito antes"

    Args:
        date_text: Texto de fecha

    Returns:
        Fecha sin sufijos ordinales
    """
    if not date_text:
        return ""

    # Regex con lookbehind: solo elimina st/nd/rd/th si hay un dígito antes
    return re.sub(r"(?<=\d)(st|nd|rd|th)", "", date_text, flags=re.IGNORECASE)


def squish_whitespace(text: str) -> str:
    """
    Reduce espacios múltiples a uno solo y hace trim.

    Args:
        text: Texto original

    Returns:
        Texto limpio
    """
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()
