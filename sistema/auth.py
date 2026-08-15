"""
Helpers compartilhados de autenticação e autorização por perfil (role).
"""
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from usuario.usuario_model import Usuario


def require_auth(request: Request) -> str:
    """Garante que há um usuário autenticado na sessão. Retorna o user_id."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user_id


def require_role(request: Request, db: Session, *roles: str) -> Usuario:
    """Garante que o usuário autenticado tem um dos perfis (roles) informados."""
    from usuario.usuario_service import UsuarioService

    user_id = require_auth(request)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user or user.role not in roles:
        raise HTTPException(status_code=403, detail="Acesso negado para o seu perfil")
    return user
