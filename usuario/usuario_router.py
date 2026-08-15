"""
Rotas da API para usuários.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from sistema.auth import require_auth, require_role
from usuario.usuario_schema import (
    UsuarioResposta, UsuarioCriar, UsuarioAtualizar, SenhaAtualizar
)
from usuario.usuario_service import UsuarioService

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


@router.get("/", response_model=List[UsuarioResposta])
def listar_usuarios(request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    return UsuarioService.listar_todos(db)


@router.get("/{user_id}", response_model=UsuarioResposta)
def obter_usuario(user_id: str, request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.post("/", response_model=UsuarioResposta)
def criar_usuario(data: UsuarioCriar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    try:
        return UsuarioService.criar(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=UsuarioResposta)
def atualizar_usuario(user_id: str, data: UsuarioAtualizar, request: Request, db: Session = Depends(get_db)):
    current_user_id = require_auth(request)
    current_user = UsuarioService.obter_por_id(db, current_user_id)
    if current_user_id != user_id and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")
    if not current_user or current_user.role != "admin":
        # Usuário comum só pode alterar o próprio nome, nunca o próprio perfil/status
        data = UsuarioAtualizar(name=data.name)
    user = UsuarioService.atualizar(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.post("/{user_id}/senha")
def alterar_senha(user_id: str, data: SenhaAtualizar, request: Request, db: Session = Depends(get_db)):
    current_user_id = require_auth(request)
    current_user = UsuarioService.obter_por_id(db, current_user_id)
    if current_user_id != user_id and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")
    try:
        success = UsuarioService.alterar_senha(db, user_id, data)
        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {"mensagem": "Senha alterada com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
def deletar_usuario(user_id: str, request: Request, db: Session = Depends(get_db)):
    current_user_id = require_auth(request)
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o próprio usuário")
    require_role(request, db, "admin")
    success = UsuarioService.deletar(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"mensagem": "Usuário excluído com sucesso"}
