"""
Schemas Pydantic para validação de profissionais.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProfissionalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    cpf: Optional[str] = None
    cns: Optional[str] = None
    cbo: Optional[str] = None
    specialty: Optional[str] = None
    team: Optional[str] = None
    active: bool = True


class ProfissionalCriar(ProfissionalBase):
    pass


class ProfissionalAtualizar(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    cns: Optional[str] = None
    cbo: Optional[str] = None
    specialty: Optional[str] = None
    team: Optional[str] = None
    active: Optional[bool] = None


class ProfissionalResposta(ProfissionalBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
