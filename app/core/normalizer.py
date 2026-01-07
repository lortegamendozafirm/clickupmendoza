"""
Normalización de datos de ClickUp.
Extrae nombre_clickup, id_mycase, nombre_normalizado desde task_name.
"""

import re
from typing import Tuple, Optional
from app.core.text_utils import normalize_name


def normalize_task_name(task_name: str) -> Tuple[str, Optional[str], str]:
    """
    Normaliza el task_name de ClickUp.

    Lógica del R:
    dvs <- dvs %>%
      mutate(
        nombre_clickup = task_name %>% str_replace("\\|.*$", "") %>% str_trim(),
        after_pipe = task_name %>% str_replace("^[^|]*\\|", "") %>% str_trim(),
        id_mycase = str_extract(after_pipe, "\\d{8}"),
        nombre_normalizado = normalize_name(nombre_clickup)
      )

    Args:
        task_name: Nombre de la tarea (formato: "Nombre Cliente | 12345678")

    Returns:
        Tupla (nombre_clickup, id_mycase, nombre_normalizado)
    """
    if not task_name:
        return ("", None, "")

    # 1. nombre_clickup: parte antes del pipe |
    if "|" in task_name:
        nombre_clickup = task_name.split("|")[0].strip()
        after_pipe = task_name.split("|", 1)[1].strip()
    else:
        nombre_clickup = task_name.strip()
        after_pipe = ""

    # 2. id_mycase: primera secuencia de 8 dígitos después del pipe
    id_mycase = None
    if after_pipe:
        match = re.search(r"\d{8}", after_pipe)
        if match:
            id_mycase = match.group(0)

    # 3. nombre_normalizado: normalizar para búsqueda fuzzy
    nombre_normalizado = normalize_name(nombre_clickup)

    return nombre_clickup, id_mycase, nombre_normalizado
