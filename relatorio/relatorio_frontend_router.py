"""
Rotas frontend para relatórios.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from relatorio.relatorio_service import RelatorioService

router = APIRouter(tags=["Frontend - Relatórios"])


@router.get("/relatorios", response_class=HTMLResponse)
def page_relatorios(request: Request, db: Session = Depends(get_db), month: str = None):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role == "operador":
        return RedirectResponse(url="/", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    data = RelatorioService.get_relatorio_completo(db, month=month)
    comparativo = RelatorioService.get_comparativo_mensal(db, n_months=12, end_month=month)
    return templates.TemplateResponse(request, "relatorios.html", {
        "user": user,
        "data": data,
        "comparativo": comparativo,
        "active_page": "relatorios",
    })
