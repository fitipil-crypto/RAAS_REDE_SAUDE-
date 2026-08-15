"""
Rotas frontend para exportação RAAS.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from usuario.usuario_service import UsuarioService
from exportacao.exportacao_service import ExportacaoService
from config.config_service import ConfigService

router = APIRouter(tags=["Frontend - Exportação"])


@router.get("/exportacao", response_class=HTMLResponse)
def page_exportacao(request: Request, month: str = Query(None), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    if not month:
        month = datetime.now().strftime("%Y-%m")

    stats = ExportacaoService.get_stats(db, month)
    config = ConfigService.get_config_estabelecimento(db) or {}
    return templates.TemplateResponse(request, "exportacao.html", {
        "user": user,
        "sel_month": month,
        "stats": stats,
        "config": config,
        "active_page": "exportacao",
    })
