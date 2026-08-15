"""
API router para logs do sistema.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from usuario.usuario_service import UsuarioService
from sistema.log_service import LogService

router = APIRouter(prefix="/api/logs", tags=["API - Logs"])


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = UsuarioService.obter_por_id(db, user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user


@router.get("/")
def listar_logs(
    request: Request,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    _require_admin(request, db)
    logs = LogService.listar_todos(
        db, action=action, user_id=user_id, resource_type=resource_type,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "user_id": l.user_id,
            "username": l.username,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "method": l.method,
            "path": l.path,
            "status_code": l.status_code,
            "details": l.details,
        }
        for l in logs
    ]


@router.get("/stats")
def stats_logs(request: Request, db: Session = Depends(get_db)):
    _require_admin(request, db)
    from collections import Counter
    logs = LogService.listar_todos(db, limit=10000)
    by_action = Counter(l.action for l in logs)
    by_resource = Counter(l.resource_type for l in logs if l.resource_type)
    by_user = Counter(l.username or "anônimo" for l in logs)
    return {
        "total": len(logs),
        "by_action": dict(by_action),
        "by_resource": dict(by_resource),
        "by_user": dict(by_user),
    }


@router.delete("/limpar")
def limpar_logs(request: Request, dias: int = 90, db: Session = Depends(get_db)):
    _require_admin(request, db)
    count = LogService.limpar_antigos(db, dias=dias)
    return {"removidos": count}
