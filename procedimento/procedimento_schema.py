"""
Schemas Pydantic para validação de procedimentos.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

CATEGORIAS_RAAS = Literal[
    "RAAS (Atenção Psicossocial)",
    "BPA Individualizado",
    "BPA Consolidado",
]


class ProcedimentoBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    category: CATEGORIAS_RAAS = Field(default="RAAS (Atenção Psicossocial)")
    active: bool = True


class ProcedimentoCriar(ProcedimentoBase):
    pass


class ProcedimentoAtualizar(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CATEGORIAS_RAAS] = None
    active: Optional[bool] = None


class ProcedimentoResposta(ProcedimentoBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
