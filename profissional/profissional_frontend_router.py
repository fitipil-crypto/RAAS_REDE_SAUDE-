"""
Rotas frontend para profissionais.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from profissional.profissional_service import ProfissionalService

router = APIRouter(tags=["Frontend - Profissionais"])


@router.get("/profissionais", response_class=HTMLResponse)
def page_profissionais(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    profissionais = ProfissionalService.listar_todos(db)
    return templates.TemplateResponse(request, "profissionais.html", {
        "user": user,
        "profissionais": profissionais,
        "active_page": "profissionais",
    })
