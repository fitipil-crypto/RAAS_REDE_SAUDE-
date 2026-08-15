"""
Rotas da API para exclusão de dados em lote.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService
from registro.registro_service import RegistroService
from sistema.auth import require_role

router = APIRouter(prefix="/api/excluir", tags=["Exclusão de Dados"])

VALID_TABLES = {"pacientes", "profissionais", "procedimentos", "registros", "registros_mes_atual"}


class ExcluirRequest(BaseModel):
    tables: List[str]
    confirm: str


@router.post("")
def excluir_dados(data: ExcluirRequest, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")

    if data.confirm != "EXCLUIR":
        raise HTTPException(status_code=400, detail="Confirmação inválida. Digite EXCLUIR.")

    targets = [t for t in data.tables if t in VALID_TABLES]
    if not targets:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma categoria válida.")

    results = {}
    for t in targets:
        if t == "pacientes":
            results[t] = PacienteService.deletar_todos(db)
        elif t == "profissionais":
            results[t] = ProfissionalService.deletar_todos(db)
        elif t == "procedimentos":
            results[t] = ProcedimentoService.deletar_todos(db)
        elif t == "registros":
            results[t] = RegistroService.deletar_todos(db)
        elif t == "registros_mes_atual":
            mes_atual = datetime.now().strftime("%Y-%m")
            results[t] = RegistroService.deletar_por_mes(db, mes_atual)

    labels = {
        "pacientes": "Pacientes",
        "profissionais": "Profissionais",
        "procedimentos": "Procedimentos",
        "registros": "Registros RAAS",
        "registros_mes_atual": "Registros do Mês Atual",
    }
    msg_parts = [f"{labels.get(t, t)}: {c}" for t, c in results.items()]
    return {"success": True, "mensagem": f"Dados excluídos — {', '.join(msg_parts)}", "results": results}
