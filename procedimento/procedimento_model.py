"""
Modelo de dados para procedimentos.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Procedimento(Base):
    __tablename__ = "procedimentos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, default="RAAS (Atenção Psicossocial)")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Procedimento(code='{self.code}', name='{self.name}')>"
