# app/models/__init__.py
"""
Modelos de datos (SQLAlchemy ORM)
"""

from app.models.lead import LeadsCache, Base
from app.models.case_assignment import CaseAssignment

__all__ = ["LeadsCache", "CaseAssignment", "Base"]