"""
Schemas Pydantic para validação de configurações.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConfiguracaoBase(BaseModel):
    chave: str = Field(..., description="Chave única da configuração")
    valor: Optional[str] = Field(None, description="Valor da configuração")
    tipo: str = Field(default="string")
    descricao: Optional[str] = None
    categoria: str = Field(default="estabelecimento")
    editavel: bool = True


class ConfiguracaoCriar(ConfiguracaoBase):
    pass


class ConfiguracaoAtualizar(BaseModel):
    valor: Optional[str] = None
    descricao: Optional[str] = None


class ConfiguracaoResposta(ConfiguracaoBase):
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfigEstabelecimento(BaseModel):
    """Schema para configurações do estabelecimento."""
    uf_code: str = Field(default="35")
    cnes_code: str = Field(default="0000000")
    organ_name: str = Field(default="CAPS MUNICIPAL")
    organ_code: str = Field(default="CAPS01")
    cnpj: str = Field(default="")
    destination_organ: str = Field(default="SECRETARIA MUNICIPAL DE SAUDE")
    destination_indicator: str = Field(default="M")
    versao: str = Field(default="02.31")
