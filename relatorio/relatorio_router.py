"""
Rotas da API para relatórios.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from relatorio.relatorio_service import RelatorioService
from sistema.auth import require_auth, require_role

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios"])


@router.get("/dashboard")
def dashboard_stats(request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    return RelatorioService.get_dashboard_stats(db)


@router.get("/completo")
def relatorio_completo(request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    return RelatorioService.get_relatorio_completo(db)


@router.get("/comparativo-mensal")
def comparativo_mensal(request: Request, n: int = 12, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    return RelatorioService.get_comparativo_mensal(db, n_months=n)
