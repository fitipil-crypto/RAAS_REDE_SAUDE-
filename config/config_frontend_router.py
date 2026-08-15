"""
Rotas frontend para configurações.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from config.config_service import ConfigService

router = APIRouter(tags=["Frontend - Configurações"])


@router.get("/configuracoes", response_class=HTMLResponse)
def page_configuracoes(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    config = ConfigService.get_config_estabelecimento(db)

    from sistema.retention_service import RetentionService
    from datetime import datetime
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    comps = []
    for i, c in enumerate(RetentionService.allowed_competencias()):
        y = c[:4]
        m = c[4:6]
        comps.append({"value": c, "label": f"{meses[int(m)-1]} de {y}", "atual": i == 0, "idx": i})

    return templates.TemplateResponse(request, "configuracoes.html", {
        "user": user,
        "config": config,
        "competencias": comps,
        "active_page": "configuracoes",
    })
