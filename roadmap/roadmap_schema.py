"""
Schemas Pydantic para validação do roadmap.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

STATUS_ROADMAP = Literal["planejado", "em_andamento", "concluido", "cancelado"]
PRIORIDADE_ROADMAP = Literal["baixa", "media", "alta"]


class RoadmapItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: STATUS_ROADMAP = Field(default="planejado")
    priority: PRIORIDADE_ROADMAP = Field(default="media")
    order: int = Field(default=0)
    done: bool = False


class RoadmapItemCriar(RoadmapItemBase):
    pass


class RoadmapItemAtualizar(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[STATUS_ROADMAP] = None
    priority: Optional[PRIORIDADE_ROADMAP] = None
    order: Optional[int] = None
    done: Optional[bool] = None


class RoadmapItemResposta(RoadmapItemBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
