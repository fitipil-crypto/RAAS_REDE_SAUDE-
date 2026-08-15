"""
Rotas frontend para registros RAAS.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from collections import defaultdict

from database import get_db
from usuario.usuario_service import UsuarioService
from registro.registro_service import RegistroService
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService
from sistema.reference_data import SRV_OPTS, CLS_OPTS, SERVICE_TYPE_MAP, DEFAULT_TEAM_CODE, DEFAULT_TEAM_NAME

router = APIRouter(tags=["Frontend - Registros"])


@router.get("/registros", response_class=HTMLResponse)
def page_registros(request: Request, month: str = Query(None), db: Session = Depends(get_db)):
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

    registros = RegistroService.listar_por_mes(db, month)
    pacientes = {p.id: p for p in PacienteService.listar_todos(db)}
    profissionais = {p.id: p for p in ProfissionalService.listar_todos(db)}
    procedimentos = {p.id: p for p in ProcedimentoService.listar_todos(db)}

    # Enrich records with display names
    for r in registros:
        proc = procedimentos.get(r.procedure_id)
        r.procedure_name = proc.name if proc else "—"
        r.professional_name = profissionais.get(r.professional_id).name if profissionais.get(r.professional_id) else "—"
        r.service_type_label = SERVICE_TYPE_MAP.get(r.service_type, "—")

    # Group by patient
    grouped = defaultdict(list)
    for r in registros:
        grouped[r.patient_id].append(r)
    groups = []
    for pid, recs in grouped.items():
        pat = pacientes.get(pid)
        groups.append({"patient": pat, "records": recs})
    groups.sort(key=lambda g: (g["patient"].name if g["patient"] else "").upper())

    # Active professionals and procedures for the form
    active_professionals = [p for p in profissionais.values() if p.active]
    active_procedures = []
    for p in procedimentos.values():
        if p.active:
            p.label = f"{p.code} — {p.name}"
            active_procedures.append(p)

    return templates.TemplateResponse(request, "registros.html", {
        "user": user,
        "registros": registros,
        "groups": groups,
        "pacientes": pacientes,
        "profissionais": profissionais,
        "procedimentos": procedimentos,
        "active_profissionais": active_professionals,
        "active_procedimentos": active_procedures,
        "sel_month": month,
        "srv_opts": SRV_OPTS,
        "cls_opts": CLS_OPTS,
        "service_type_map": SERVICE_TYPE_MAP,
        "default_team_code": DEFAULT_TEAM_CODE,
        "default_team_name": DEFAULT_TEAM_NAME,
        "active_page": "registros",
    })
