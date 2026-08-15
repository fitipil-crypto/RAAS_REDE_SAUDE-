"""
Modelo de dados para configurações do sistema.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    tipo = Column(String(50), nullable=False, default="string")
    descricao = Column(Text, nullable=True)
    categoria = Column(String(50), nullable=False, default="estabelecimento")
    editavel = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Configuracao(chave='{self.chave}', valor='{self.valor}')>"
