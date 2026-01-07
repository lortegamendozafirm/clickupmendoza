"""
Modelo principal: leads_cache
Wide table con campos nativos de ClickUp + campos minados del contenido
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class LeadsCache(Base):
    """
    Tabla principal que almacena leads de ClickUp con datos parseados.
    Incluye metadatos nativos + campos extraídos del task_content.
    """

    __tablename__ = "leads_cache"

    # ========================================================================
    # IDENTIFICADORES (PK + extraídos)
    # ========================================================================
    task_id = Column(String(50), primary_key=True, nullable=False, index=True)
    id_mycase = Column(String(20), nullable=True, index=True, comment="Extraído del texto")
    mycase_link = Column(String(500), nullable=True, comment="URL de MyCase")

    # ========================================================================
    # METADATOS CLICKUP (nativos)
    # ========================================================================
    task_name = Column(Text, nullable=True, comment="Nombre original de la tarea")
    status = Column(String(100), nullable=True, comment="Estado de la tarea")
    priority = Column(String(50), nullable=True, comment="Prioridad")
    created_by = Column(String(200), nullable=True, comment="Creador de la tarea")
    assignee = Column(Text, nullable=True, comment="Asignado (puede ser JSON o texto)")

    date_created = Column(DateTime(timezone=True), nullable=True, index=True)
    date_updated = Column(DateTime(timezone=True), nullable=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)

    # ========================================================================
    # CAMPOS DE NEGOCIO / PIPELINE
    # ========================================================================
    pipeline_de_viabilidad = Column(String(200), nullable=True)
    fecha_consulta_original = Column(DateTime(timezone=True), nullable=True)
    tis_open = Column(Boolean, nullable=True)

    # ========================================================================
    # CAMPOS NORMALIZADOS PARA BÚSQUEDA
    # ========================================================================
    nombre_clickup = Column(Text, nullable=True, comment="Parte antes del pipe |")
    nombre_normalizado = Column(
        String(500),
        nullable=True,
        index=True,
        comment="ASCII, mayúsculas, alfanumérico para búsqueda fuzzy"
    )

    # ========================================================================
    # MINING DESDE task_content (datos extraídos por regex)
    # ========================================================================
    full_name_extracted = Column(String(500), nullable=True, comment="Name: extraído")
    phone_raw = Column(String(100), nullable=True, comment="Teléfono sin limpiar")
    phone_number = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Solo dígitos, validado (10-15 chars)"
    )
    email_extracted = Column(String(255), nullable=True, comment="Email extraído")
    location = Column(Text, nullable=True, comment="Ubicación (bloque)")

    interviewee = Column(String(500), nullable=True, comment="Quién fue entrevistado")
    interview_type = Column(String(100), nullable=True, comment="Individual/Combo")
    interview_result = Column(String(100), nullable=True, comment="Done/Reschedule/...")
    interview_other = Column(Text, nullable=True, comment="Bloque de 'Other result...'")

    case_type = Column(String(200), nullable=True, comment="Tipo de caso")
    accident_last_2y = Column(String(10), nullable=True, comment="yes/no normalizado")
    video_call = Column(String(10), nullable=True, comment="yes/no normalizado")

    # Campos opcionales adicionales (del R script)
    record_criminal = Column(String(100), nullable=True)
    joint_residences = Column(String(100), nullable=True)
    eoir_pending = Column(String(100), nullable=True)
    tvisa_min_wage = Column(String(100), nullable=True)
    referral_full_name = Column(String(500), nullable=True)
    referral_phone_number = Column(String(20), nullable=True)

    # ========================================================================
    # CONTENIDO COMPLETO
    # ========================================================================
    task_content = Column(Text, nullable=True, comment="Descripción completa (puede contener PII)")
    comment_count = Column(Integer, nullable=True, default=0)

    # === AGREGAR ESTAS LÍNEAS ===
    task_type = Column(String(50), nullable=True, comment="Tipo de tarea")
    space_name = Column(String(100), nullable=True)
    folder_name = Column(String(100), nullable=True)
    list_name = Column(String(100), nullable=True)
    consult_notice = Column(String(100), nullable=True)
    latest_comment = Column(Text, nullable=True, comment="Último comentario (puede ser muy largo)")
    # ============================

    
    # ========================================================================
    # TIMESTAMPS INTERNOS
    # ========================================================================
    synced_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Última vez que se sincronizó desde ClickUp"
    )

    # ========================================================================
    # ÍNDICES
    # ========================================================================
    __table_args__ = (
        # Índice GIN para búsqueda trigram fuzzy (pg_trgm)
        # Se crea vía migración SQL directa porque SQLAlchemy no lo soporta nativamente
        # CREATE INDEX idx_nombre_normalizado_gin ON leads_cache USING gin (nombre_normalizado gin_trgm_ops);
        Index("idx_task_id", "task_id"),
        Index("idx_id_mycase", "id_mycase"),
        Index("idx_phone_number", "phone_number"),
        Index("idx_date_updated", "date_updated"),
    )

    def __repr__(self):
        return f"<LeadsCache(task_id={self.task_id}, nombre={self.nombre_clickup})>"
