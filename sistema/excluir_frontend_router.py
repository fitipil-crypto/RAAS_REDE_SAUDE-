"""
Rotas frontend para exclusão de dados.
"""
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService
from registro.registro_service import RegistroService

router = APIRouter(tags=["Frontend - Exclusão"])


@router.get("/excluir", response_class=HTMLResponse)
def page_excluir(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse(url="/", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    mes_atual = datetime.now().strftime("%Y-%m")
    counts = {
        "pacientes": len(PacienteService.listar_todos(db)),
        "profissionais": len(ProfissionalService.listar_todos(db)),
        "procedimentos": len(ProcedimentoService.listar_todos(db)),
        "registros": len(RegistroService.listar_todos(db)),
        "registros_mes_atual": RegistroService.contar_por_mes(db, mes_atual),
    }
    return templates.TemplateResponse(request, "excluir.html", {
        "user": user,
        "counts": counts,
        "active_page": "excluir",
    })
