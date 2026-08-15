"""
Rotas frontend para procedimentos.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from procedimento.procedimento_service import ProcedimentoService

router = APIRouter(tags=["Frontend - Procedimentos"])


@router.get("/procedimentos", response_class=HTMLResponse)
def page_procedimentos(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    procedimentos = ProcedimentoService.listar_todos(db)
    return templates.TemplateResponse(request, "procedimentos.html", {
        "user": user,
        "procedimentos": procedimentos,
        "active_page": "procedimentos",
    })
