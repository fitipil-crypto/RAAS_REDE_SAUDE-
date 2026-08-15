"""
Modelo de dados para profissionais.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    name = Column(String(200), nullable=False)
    cpf = Column(String(14), nullable=True)
    cns = Column(String(20), nullable=True, index=True)
    cbo = Column(String(10), nullable=True)
    specialty = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Profissional(name='{self.name}', cns='{self.cns}')>"
