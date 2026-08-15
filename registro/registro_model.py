"""
Modelo de dados para registros RAAS.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.sql import func
from database import Base


class Registro(Base):
    __tablename__ = "registros_raas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    service_month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    service_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    patient_id = Column(String(36), nullable=False, index=True)
    professional_id = Column(String(36), nullable=True, index=True)
    procedure_id = Column(String(36), nullable=False, index=True)
    cbo_code = Column(String(10), nullable=True)
    service_type = Column(String(2), nullable=True, default="01")
    local_realizacao = Column(String(1), nullable=True, default="C")  # C=CAPS, T=Território
    authorization = Column(String(20), nullable=True)
    srv = Column(String(3), nullable=True, default="115")
    cls = Column(String(3), nullable=True, default="002")
    team_code = Column(String(10), nullable=True)
    team_type = Column(String(3), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Registro(month='{self.service_month}', patient='{self.patient_id}')>"
