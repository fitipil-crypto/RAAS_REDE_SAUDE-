"""
Modelo de dados para usuários do sistema.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="operador")  # admin, operador, coordenador
    password_hash = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Usuario(username='{self.username}', role='{self.role}')>"
