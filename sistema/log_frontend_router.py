"""
Frontend router para logs do sistema.
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from usuario.usuario_service import UsuarioService
from sistema.log_service import LogService

router = APIRouter(tags=["Frontend - Logs"])
templates = Jinja2Templates(directory="templates")


@router.get("/logs", response_class=HTMLResponse)
def page_logs(
    request: Request,
    db: Session = Depends(get_db),
    action: str = None,
    resource_type: str = None,
    date_from: str = None,
    date_to: str = None,
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    logs = LogService.listar_todos(
        db, action=action, resource_type=resource_type,
        date_from=date_from, date_to=date_to, limit=200,
    )

    # Estatísticas rápidas
    from collections import Counter
    by_action = Counter(l.action for l in logs)
    by_resource = Counter(l.resource_type for l in logs if l.resource_type)

    action_labels = {
        "LOGIN": "Entrada",
        "LOGOUT": "Saída",
        "CREATE": "Criação",
        "UPDATE": "Atualização",
        "DELETE": "Exclusão",
        "VIEW": "Visualização",
        "EXPORT": "Exportação",
        "IMPORT": "Importação",
        "BACKUP": "Backup",
        "CONFIG": "Configuração",
    }

    resource_labels = {
        "paciente": "Paciente",
        "profissional": "Profissional",
        "procedimento": "Procedimento",
        "registro": "Registro RAAS",
        "usuario": "Usuário",
        "config": "Configuração",
        "importacao": "Importação",
        "exportacao": "Exportação",
        "backup": "Backup",
        "relatorio": "Relatório",
        "roadmap": "Roadmap",
    }

    return templates.TemplateResponse(request, "logs.html", {
        "user": user,
        "logs": logs,
        "active_page": "logs",
        "filter_action": action,
        "filter_resource": resource_type,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "by_action": dict(by_action),
        "by_resource": dict(by_resource),
        "action_labels": action_labels,
        "resource_labels": resource_labels,
    })
