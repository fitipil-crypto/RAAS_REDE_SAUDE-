"""
Schemas Pydantic para validação de registros RAAS.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RegistroBase(BaseModel):
    service_month: str = Field(..., description="Competência YYYY-MM")
    service_date: str = Field(..., description="Data do atendimento YYYY-MM-DD")
    patient_id: str = Field(..., description="ID do paciente")
    professional_id: Optional[str] = None
    procedure_id: str = Field(..., description="ID do procedimento")
    cbo_code: Optional[str] = None
    service_type: str = Field(default="01")
    local_realizacao: str = Field(default="C")
    authorization: Optional[str] = None
    srv: str = Field(default="115")
    cls: str = Field(default="002")
    team_code: Optional[str] = None
    team_type: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class RegistroCriar(RegistroBase):
    pass


class RegistroAtualizar(BaseModel):
    service_month: Optional[str] = None
    service_date: Optional[str] = None
    patient_id: Optional[str] = None
    professional_id: Optional[str] = None
    procedure_id: Optional[str] = None
    cbo_code: Optional[str] = None
    service_type: Optional[str] = None
    local_realizacao: Optional[str] = None
    authorization: Optional[str] = None
    srv: Optional[str] = None
    cls: Optional[str] = None
    team_code: Optional[str] = None
    team_type: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None


class RegistroResposta(RegistroBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
