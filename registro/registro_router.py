"""
Rotas da API para registros RAAS.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from registro.registro_schema import RegistroResposta, RegistroCriar, RegistroAtualizar
from registro.registro_service import RegistroService
from sistema.auth import require_auth, require_role

router = APIRouter(prefix="/api/registros", tags=["Registros RAAS"])


@router.get("/", response_model=List[RegistroResposta])
def listar_registros(request: Request, month: str = Query(None), db: Session = Depends(get_db)):
    require_auth(request)
    return RegistroService.listar_todos(db, month)


@router.get("/{registro_id}", response_model=RegistroResposta)
def obter_registro(registro_id: str, request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    reg = RegistroService.obter_por_id(db, registro_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return reg


@router.post("/", response_model=RegistroResposta)
def criar_registro(data: RegistroCriar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador")
    return RegistroService.criar(db, data)


@router.post("/varios", response_model=List[RegistroResposta])
def criar_varios_registros(registros: List[RegistroCriar], request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador")
    return RegistroService.criar_varios(db, registros)


@router.put("/{registro_id}", response_model=RegistroResposta)
def atualizar_registro(registro_id: str, data: RegistroAtualizar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador")
    reg = RegistroService.atualizar(db, registro_id, data)
    if not reg:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return reg


@router.delete("/{registro_id}")
def deletar_registro(registro_id: str, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    success = RegistroService.deletar(db, registro_id)
    if not success:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return {"mensagem": "Registro excluído com sucesso"}


@router.post("/deletar-varios")
def deletar_varios(ids: List[str], request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    count = RegistroService.deletar_varios(db, ids)
    return {"mensagem": f"{count} registro(s) excluído(s)"}
