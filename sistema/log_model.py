"""
Modelo de dados para logs do sistema (auditoria).
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from database import Base


class LogSistema(Base):
    __tablename__ = "logs_sistema"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, VIEW, EXPORT, IMPORT, BACKUP, CONFIG
    resource_type = Column(String(50), nullable=True)  # paciente, profissional, procedimento, registro, usuario, config, etc.
    resource_id = Column(String(36), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    path = Column(String(255), nullable=True)
    status_code = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Log(action='{self.action}', user='{self.username}', resource='{self.resource_type}')>"
