"""
Motor de parsing de task_content.
Extrae campos estructurados del texto libre usando regex.

Replica la lógica del script de R:
- get_line(): extrae campos de una línea (Label: Value)
- get_block_until(): extrae bloques multilínea entre dos labels
- get_location(): extracción especial de Location
- get_mycase_id(): extrae ID de MyCase
"""

import re
from typing import Optional
from app.core.text_utils import squish_whitespace, clean_phone


def _escape_regex(text: str) -> str:
    """Escapa metacaracteres de regex"""
    return re.escape(text)


def get_line(text: str, label: str) -> Optional[str]:
    """
    Extrae un campo de UNA sola línea con patrón: Label: Value

    Patrón regex (equivalente a R):
    (?m)^{label}\s*\??\s*:+[[:blank:]]*(.*)$

    Args:
        text: Contenido completo
        label: Etiqueta a buscar (ej: "Name", "Phone")

    Returns:
        Valor extraído o None
    """
    if not text or not label:
        return None

    escaped_label = _escape_regex(label)

    # (?m): multiline mode (^ y $ por línea)
    # \s*\??\s*:+ : permite espacios, "?" opcional, y ":" (uno o más)
    # [[:blank:]]* en Python es [ \t]*
    # (.*) captura el resto de la línea
    pattern = rf"(?m)^{escaped_label}\s*\??\s*:+[ \t]*(.*)$"

    match = re.search(pattern, text)
    if match:
        value = match.group(1)
        value = squish_whitespace(value)
        return value if value else None

    return None


def get_block_until(text: str, start_label: str, end_label: str) -> Optional[str]:
    """
    Extrae un BLOQUE de texto multilínea entre dos labels.

    Patrón regex (equivalente a R):
    (?ms)^{start_label}\s*\??\s*:+[ \t]*(.*?)\s*(?=^{end_label}\s*\??\s*:+)

    Flags:
    - (?ms): multiline + dotall (. incluye \n)
    - .*? : captura no-greedy (hasta encontrar end_label)
    - (?=...) : lookahead (no consume el end_label)

    Args:
        text: Contenido completo
        start_label: Label inicial
        end_label: Label final (no se incluye)

    Returns:
        Bloque extraído o None
    """
    if not text or not start_label or not end_label:
        return None

    s = _escape_regex(start_label)
    e = _escape_regex(end_label)

    pattern = rf"(?ms)^{s}\s*\??\s*:+[ \t]*(.*?)\s*(?=^{e}\s*\??\s*:+)"

    match = re.search(pattern, text)
    if match:
        value = match.group(1)
        # Eliminar \r si existe (Windows line endings)
        value = value.replace("\r", "")
        value = value.strip()
        return value if value else None

    return None


def get_location(text: str) -> Optional[str]:
    """
    Extracción especial de Location (formato específico con ====).

    Patrón del R:
    (?ms)^Location\s*\n=+\s*\n(.*?)\s*(?:\n\s*\n|$)

    Busca:
    Location
    =======
    [contenido]

    Args:
        text: Contenido completo

    Returns:
        Location extraída o None
    """
    if not text:
        return None

    pattern = r"(?ms)^Location\s*\n=+\s*\n(.*?)\s*(?:\n\s*\n|$)"

    match = re.search(pattern, text)
    if match:
        value = match.group(1)
        value = value.replace("\r", "")
        value = value.strip()
        return value if value else None

    return None


def get_mycase_id(text: str) -> Optional[str]:
    """
    Extrae ID de MyCase (8 dígitos).

    Busca en dos lugares:
    1. "My Case ID: 12345678"
    2. "mycase.com/leads/12345678"

    Args:
        text: Contenido completo

    Returns:
        ID (8 dígitos) o None
    """
    if not text:
        return None

    # Intento 1: My Case ID: [8 dígitos]
    pattern1 = r"(?m)^My Case ID.*?:\s*(\d{8})\b"
    match1 = re.search(pattern1, text, re.IGNORECASE)
    if match1:
        return match1.group(1)

    # Intento 2: mycase.com/leads/[8 dígitos]
    pattern2 = r"mycase\.com/leads/(\d{8})\b"
    match2 = re.search(pattern2, text, re.IGNORECASE)
    if match2:
        return match2.group(1)

    return None


def parse_task_content(content: str) -> dict:
    """
    Parsea el task_content completo y devuelve un diccionario con todos los campos.

    Replica la lógica del script R: dvs_clean <- dvs %>% mutate(...)

    Args:
        content: task_content (descripción de la tarea)

    Returns:
        Diccionario con campos parseados
    """
    if not content:
        return {}

    # Normalizar contenido vacío/basura (del R script)
    if content.strip() in ["\n", "\n\n \n\n", "/\n", "/\n\n"]:
        return {}

    result = {}

    # ========================================================================
    # CAMPOS DE LÍNEA SIMPLE
    # ========================================================================
    result["full_name_extracted"] = get_line(content, "Name")
    result["phone_raw"] = get_line(content, "Phone")
    result["email_extracted"] = get_line(content, "Email")
    result["interviewee"] = get_line(content, "Interviewee")
    result["interview_result"] = get_line(content, "Result of interview")
    result["interview_type"] = get_line(content, "Type of Interview")
    result["mycase_link"] = get_line(content, "My Case link")
    result["case_type"] = get_line(content, "Tipo de caso")
    result["video_call"] = get_line(content, "¿Fue videollamada?")
    result["accident_last_2y"] = get_line(
        content,
        "El cliente menciono haber  sufrido algún accidente como accidente vehicular, "
        "mala praxis medica, accidentes en el trabajo, producto defectuoso, "
        "resbalón y caida en algún establecimiento en los últimos 2 años?"
    )

    # Campos opcionales
    result["record_criminal"] = get_line(content, "Record Criminal")
    result["joint_residences"] = get_line(content, "Cumple con Joint Residences (Hijos o Espos@s)")
    result["eoir_pending"] = get_line(content, "Tiene cortes migratorias pendientes (EOIR)")
    result["tvisa_min_wage"] = get_line(content, "Si es Visa T cumple con el sueldo minimo")
    result["referral_full_name"] = get_line(content, "Nombre completo del referido")

    # ========================================================================
    # CAMPOS ESPECIALES (bloques / extracciones complejas)
    # ========================================================================
    result["location"] = get_location(content)
    result["mycase_id"] = get_mycase_id(content)

    # Bloque interview_other: captura entre "Other result..." y "Type of Interview"
    # con fallback a "Proceso por el que califica" o bloque "VAWA"
    interview_other = (
        get_block_until(
            content,
            "Other result of interview (optional, explain why it wasn't completed)",
            "Type of Interview"
        )
        or get_line(content, "Proceso por el que califica")
        or get_block_until(content, "VAWA", "Type of Interview")
    )
    result["interview_other"] = interview_other

    # ========================================================================
    # LIMPIEZA Y VALIDACIÓN
    # ========================================================================

    # Teléfono: validar y limpiar
    phone_clean = clean_phone(result.get("phone_raw"))
    result["phone_number"] = phone_clean

    # Teléfono del referido
    referral_phone_raw = get_line(content, "Telefono del referido")
    referral_phone_clean = clean_phone(referral_phone_raw)
    result["referral_phone_number"] = referral_phone_clean

    # Normalizar yes/no a minúsculas
    if result.get("video_call"):
        result["video_call"] = result["video_call"].lower()
    if result.get("accident_last_2y"):
        result["accident_last_2y"] = result["accident_last_2y"].lower()

    return result
