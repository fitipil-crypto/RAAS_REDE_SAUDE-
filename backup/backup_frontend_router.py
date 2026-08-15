"""
Rotas frontend para backup.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService
from registro.registro_service import RegistroService

router = APIRouter(tags=["Frontend - Backup"])


@router.get("/backup", response_class=HTMLResponse)
def page_backup(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    stats = {
        "pacientes": len(PacienteService.listar_todos(db)),
        "profissionais": len(ProfissionalService.listar_todos(db)),
        "procedimentos": len(ProcedimentoService.listar_todos(db)),
        "registros": len(RegistroService.listar_todos(db)),
    }
    return templates.TemplateResponse(request, "backup.html", {
        "user": user,
        "stats": stats,
        "active_page": "backup",
    })
