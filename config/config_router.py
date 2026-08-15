"""
Rotas da API para configurações.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from config.config_schema import (
    ConfiguracaoResposta, ConfiguracaoCriar, ConfiguracaoAtualizar, ConfigEstabelecimento
)
from config.config_service import ConfigService

router = APIRouter(prefix="/api/configuracoes", tags=["Configurações"])


def _require_auth(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user_id


@router.get("/", response_model=List[ConfiguracaoResposta])
def listar_configuracoes(request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    return ConfigService.listar_todas(db)


@router.get("/estabelecimento")
def obter_config_estabelecimento(request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    return ConfigService.get_config_estabelecimento(db)


@router.put("/estabelecimento")
def atualizar_config_estabelecimento(data: ConfigEstabelecimento, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    result = ConfigService.atualizar_varios(db, data.model_dump())
    return {"mensagem": "Configurações salvas com sucesso", "result": result}


@router.get("/{chave}", response_model=ConfiguracaoResposta)
def obter_configuracao(chave: str, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    config = ConfigService.obter_por_chave(db, chave)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config


@router.post("/", response_model=ConfiguracaoResposta)
def criar_configuracao(data: ConfiguracaoCriar, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    existe = ConfigService.obter_por_chave(db, data.chave)
    if existe:
        raise HTTPException(status_code=400, detail="Configuração já existe")
    return ConfigService.criar(db, data)


@router.put("/{chave}", response_model=ConfiguracaoResposta)
def atualizar_configuracao(chave: str, data: ConfiguracaoAtualizar, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    config = ConfigService.atualizar(db, chave, data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config


@router.delete("/{chave}")
def deletar_configuracao(chave: str, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    success = ConfigService.deletar(db, chave)
    if not success:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return {"mensagem": "Configuração deletada com sucesso"}
