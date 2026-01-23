#app/models/lead.py
"""
Modelo principal: leads_cache
Versión Homologada con CSV de Exportación y Análisis R.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timezone

Base = declarative_base()

class LeadsCache(Base):
    """
    Tabla principal que almacena leads de ClickUp con datos parseados.
    Diseñada para recibir datos crudos del CSV y datos limpios del Parser.
    """

    __tablename__ = "leads_cache"

    # ========================================================================
    # 1. IDENTIFICADORES Y CLAVES
    # ========================================================================
    task_id = Column(String(50), primary_key=True, nullable=False, index=True)
    id_mycase = Column(String(255), nullable=True, index=True, comment="ID numérico de MyCase")
    mycase_link = Column(String(500), nullable=True, comment="URL directa")

    # ========================================================================
    # 2. METADATOS CLICKUP (Nativos)
    # ========================================================================
    task_name = Column(Text, nullable=True, comment="Nombre original")
    status = Column(String(255), nullable=True)
    priority = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    assignee = Column(Text, nullable=True, comment="Puede contener múltiples nombres")
    
    # Estructura (Space/Folder/List) - Detectados en tu análisis R
    space_name = Column(String(255), nullable=True)
    folder_name = Column(String(255), nullable=True)
    list_name = Column(String(255), nullable=True)
    task_type = Column(String(100), nullable=True)

    # Fechas
    date_created = Column(DateTime(timezone=True), nullable=True, index=True)
    date_updated = Column(DateTime(timezone=True), nullable=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    date_closed = Column(DateTime(timezone=True), nullable=True)

    # ========================================================================
    # 3. DATOS DEL NEGOCIO (Mapeados desde CSV + Mining)
    # ========================================================================
    # Pipeline y Estado
    pipeline_de_viabilidad = Column(String(255), nullable=True)
    fecha_consulta_original = Column(DateTime(timezone=True), nullable=True)
    tis_open = Column(Boolean, nullable=True, default=False)
    
    # Entrevista / Intake
    consult_notice = Column(String(255), nullable=True, comment="Aviso de Consulta")
    interviewee = Column(String(255), nullable=True)
    interview_type = Column(String(255), nullable=True, comment="Individual/Combo")
    interview_result = Column(String(255), nullable=True)
    interview_other = Column(Text, nullable=True, comment="Motivos de no completado/otros")
    
    # Datos del Caso
    case_type = Column(String(255), nullable=True)
    accident_last_2y = Column(String(255), nullable=True, comment="yes/no normalizado")
    video_call = Column(String(255), nullable=True, comment="yes/no normalizado")
    record_criminal = Column(String(255), nullable=True)
    joint_residences = Column(String(255), nullable=True)
    eoir_pending = Column(String(255), nullable=True)
    tvisa_min_wage = Column(String(255), nullable=True)

    # Referidos
    referral_full_name = Column(String(255), nullable=True)
    referral_phone_number = Column(String(255), nullable=True)

    # ========================================================================
    # 4. DATOS DE CONTACTO (Extraídos / Normalizados)
    # ========================================================================
    full_name_extracted = Column(String(255), nullable=True)
    phone_raw = Column(String(255), nullable=True)
    phone_number = Column(String(255), nullable=True, index=True, comment="Solo dígitos")
    email_extracted = Column(String(255), nullable=True)
    location = Column(Text, nullable=True)

    # ========================================================================
    # 5. CAMPOS DE BÚSQUEDA NORMALIZADA
    # ========================================================================
    nombre_clickup = Column(Text, nullable=True)
    nombre_normalizado = Column(
        String(500),
        nullable=True,
        index=True,
        comment="NORMALIZADO PARA BÚSQUEDA FUZZY (SIN ACENTOS)"
    )

    # ========================================================================
    # 6. CONTENIDO PESADO (Large Text)
    # ========================================================================
    task_content = Column(Text, nullable=True, comment="Descripción completa")
    latest_comment = Column(Text, nullable=True, comment="Último comentario (puede ser enorme)")
    comment_count = Column(Integer, default=0)

    # ========================================================================
    # 7. METADATOS DE SISTEMA
    # ========================================================================
    synced_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Configuración de Índices para optimización
    __table_args__ = (
        Index("idx_task_id", "task_id"),
        Index("idx_id_mycase", "id_mycase"),
        Index("idx_phone_search", "phone_number"),
        # Índice GIN para búsqueda de texto (requiere extensión pg_trgm)
        # Se crea manualmente en init_db.py, pero SQLAlchemy lo puede definir aquí si usas dialectos
        # Index('idx_leads_nombre_trgm', nombre_normalizado, postgresql_ops={"nombre_normalizado": "gin_trgm_ops"}),
    )

    def __repr__(self):
        return f"<LeadsCache(id={self.task_id}, status={self.status})>"