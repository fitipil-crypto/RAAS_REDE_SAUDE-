"""
Rotas frontend para usuários (Controle de Acesso).
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService

router = APIRouter(tags=["Frontend - Usuários"])


def _get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return UsuarioService.obter_por_id(db, user_id)


@router.get("/acesso", response_class=HTMLResponse)
def page_acesso(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    users = UsuarioService.listar_todos(db)
    return templates.TemplateResponse(request, "acesso.html", {
        "user": user,
        "users": users,
        "active_page": "acesso",
    })
