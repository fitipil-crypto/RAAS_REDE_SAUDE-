"""
Schemas Pydantic para validação de usuários.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100, description="Login do usuário")
    name: str = Field(..., min_length=1, max_length=200, description="Nome completo")
    role: str = Field(default="operador", description="Perfil: admin, operador, coordenador")
    active: bool = Field(default=True, description="Usuário ativo")


class UsuarioCriar(UsuarioBase):
    password: str = Field(..., min_length=3, description="Senha (mínimo 3 caracteres)")


class UsuarioAtualizar(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class SenhaAtualizar(BaseModel):
    current_password: Optional[str] = Field(None, description="Senha atual (obrigatório para próprio usuário)")
    new_password: str = Field(..., min_length=3, description="Nova senha")
    confirm_password: str = Field(..., description="Confirmação da nova senha")


class UsuarioResposta(UsuarioBase):
    id: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
