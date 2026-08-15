"""
Rotas frontend para pacientes.
"""
from datetime import date
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from paciente.paciente_service import PacienteService
from config.config_service import ConfigService
from sistema.reference_data import get_municipio

router = APIRouter(tags=["Frontend - Pacientes"])


def _calcular_idade(birth_date: str) -> int | None:
    try:
        y, m, d = (int(p) for p in birth_date.split("-"))
        nasc = date(y, m, d)
    except (ValueError, AttributeError):
        return None
    hoje = date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))


@router.get("/pacientes", response_class=HTMLResponse)
def page_pacientes(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    pacientes = PacienteService.listar_todos(db)
    return templates.TemplateResponse(request, "pacientes.html", {
        "user": user,
        "pacientes": pacientes,
        "default_city": ConfigService.obter_valor(db, "default_city", ""),
        "default_state": ConfigService.obter_valor(db, "default_state", ""),
        "default_municipality_code": ConfigService.obter_valor(db, "default_municipality_code", ""),
        "active_page": "pacientes",
    })


@router.get("/pacientes/{paciente_id}", response_class=HTMLResponse)
def page_paciente_detalhe(paciente_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    paciente = PacienteService.obter_por_id(db, paciente_id)
    if not paciente:
        return RedirectResponse(url="/pacientes", status_code=302)

    municipio_nome, municipio_uf = get_municipio(paciente.municipality_code)
    return templates.TemplateResponse(request, "paciente_detalhe.html", {
        "user": user,
        "paciente": paciente,
        "idade": _calcular_idade(paciente.birth_date),
        "municipio_nome": municipio_nome,
        "municipio_uf": municipio_uf,
        "default_city": ConfigService.obter_valor(db, "default_city", ""),
        "default_state": ConfigService.obter_valor(db, "default_state", ""),
        "default_municipality_code": ConfigService.obter_valor(db, "default_municipality_code", ""),
        "active_page": "pacientes",
    })
