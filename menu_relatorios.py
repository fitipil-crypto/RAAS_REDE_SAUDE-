"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO "RELATÓRIOS" — Extração consolidada em Python
═══════════════════════════════════════════════════════════════════════════════

Reúne, num único lugar, todo o código Python do módulo de Relatórios do projeto
saude_raas (FastAPI + SQLAlchemy).

No projeto original, este código está distribuído em 3 arquivos:
    relatorio/relatorio_service.py          → Cálculo de estatísticas e indicadores
    relatorio/relatorio_router.py           → Rotas da API REST (/api/relatorios)
    relatorio/relatorio_frontend_router.py  → Rota da página HTML (/relatorios)

O módulo agrega dados de registros, pacientes, profissionais e procedimentos
para gerar indicadores de produção, demografia e distribuições, tanto para o
dashboard quanto para a tela de relatórios (com filtro opcional por competência).
"""

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Serviços de outras entidades usados pelo relatório
from registro.registro_service import RegistroService
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService, get_sigtap_name
from usuario.usuario_service import UsuarioService
from database import get_db


# ═════════════════════════════════════════════════════════════════════════════
# 1. SERVIÇO  (relatorio/relatorio_service.py)
#    Toda a lógica de cálculo de indicadores e estatísticas.
# ═════════════════════════════════════════════════════════════════════════════
class RelatorioService:

    # ── Números-resumo do dashboard ──────────────────────────────────────────
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        return {
            "total_pacientes": len(PacienteService.listar_todos(db)),
            "total_profissionais": len(ProfissionalService.listar_todos(db, ativos_only=True)),
            "total_procedimentos": len(ProcedimentoService.listar_todos(db, ativos_only=True)),
            "total_registros": len(RegistroService.listar_todos(db)),
        }

    # ── Cálculo de idade a partir da data de nascimento (YYYY-MM-DD) ──────────
    @staticmethod
    def _calc_age(birth_date: str) -> int | None:
        if not birth_date:
            return None
        try:
            bd = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            return age if age >= 0 else None
        except (ValueError, TypeError):
            return None

    # ── Faixa etária a partir da idade ────────────────────────────────────────
    @staticmethod
    def _age_group(age: int | None) -> str:
        if age is None:
            return "Não informado"
        if age < 18:
            return "0-17 anos"
        if age < 30:
            return "18-29 anos"
        if age < 45:
            return "30-44 anos"
        if age < 60:
            return "45-59 anos"
        return "60+ anos"

    # ── Relatório completo (usado na tela de Relatórios) ──────────────────────
    @staticmethod
    def get_relatorio_completo(db: Session, month: str = None) -> dict:
        registros = RegistroService.listar_todos(db)
        pacientes = {p.id: p for p in PacienteService.listar_todos(db)}
        profissionais = {p.id: p for p in ProfissionalService.listar_todos(db)}
        procedimentos = {p.id: p for p in ProcedimentoService.listar_todos(db)}

        # Filtro opcional por competência (YYYY-MM)
        if month:
            registros = [r for r in registros if r.service_month == month]

        # ── Estatísticas básicas ──
        total_atendimentos = sum(r.quantity or 1 for r in registros)
        pacientes_ativos_ids = {r.patient_id for r in registros}
        pacientes_ativos = len(pacientes_ativos_ids)

        # Novos pacientes: no mês do filtro, ou nos últimos 30 dias
        if month:
            new_patients = sum(
                1 for p in pacientes.values()
                if p.created_at and p.created_at.strftime("%Y-%m") == month
            )
        else:
            cutoff = datetime.now() - timedelta(days=30)
            new_patients = sum(
                1 for p in pacientes.values()
                if p.created_at and p.created_at >= cutoff
            )

        # ── Top 10 profissionais (por quantidade de atendimentos) ──
        by_prof = Counter()
        for r in registros:
            if r.professional_id:
                prof = profissionais.get(r.professional_id)
                if prof:
                    by_prof[prof.name] += r.quantity or 1
        top_profs = by_prof.most_common(10)

        # ── Top 10 procedimentos (nome oficial SIGTAP) ──
        by_proc = Counter()
        for r in registros:
            proc = procedimentos.get(r.procedure_id)
            if proc:
                name = get_sigtap_name(proc.code) or proc.name
                by_proc[name] += r.quantity or 1
        top_procs = by_proc.most_common(10)

        # ── Atendimentos por mês (últimos 6, sobre TODOS os registros) ──
        now = datetime.now()
        months = []
        for i in range(5, -1, -1):
            d = now - timedelta(days=i * 30)
            month_key = d.strftime("%Y-%m")
            months.append(month_key)

        all_registros = RegistroService.listar_todos(db)
        month_counts = Counter()
        for r in all_registros:
            month_counts[r.service_month] += r.quantity or 1

        monthly = [{"month": m, "count": month_counts.get(m, 0)} for m in months]

        # ── Demografia: gênero (dos pacientes ativos) ──
        gender_counts = Counter()
        for pid in pacientes_ativos_ids:
            p = pacientes.get(pid)
            if p:
                g = p.gender or "Não informado"
                gender_counts[
                    "Masculino" if g == "M" else "Feminino" if g == "F" else "Não informado"
                ] += 1

        # ── Demografia: faixas etárias ──
        age_groups = Counter()
        for pid in pacientes_ativos_ids:
            p = pacientes.get(pid)
            if p:
                age = RelatorioService._calc_age(p.birth_date)
                age_groups[RelatorioService._age_group(age)] += 1

        # ── Distribuição de CID principal (top 10) ──
        cid_counts = Counter()
        for pid in pacientes_ativos_ids:
            p = pacientes.get(pid)
            if p and p.cid_main:
                cid_counts[p.cid_main] += 1
        top_cids = cid_counts.most_common(10)

        # ── Distribuição por tipo de serviço ──
        service_type_counts = Counter()
        service_type_labels = {"01": "Consulta", "02": "Visita Domiciliar", "03": "Atividade Coletiva"}
        for r in registros:
            label = service_type_labels.get(r.service_type or "01", r.service_type or "01")
            service_type_counts[label] += r.quantity or 1

        # ── Distribuição por local de realização (CAPS / Território) ──
        local_counts = Counter()
        local_labels = {"C": "CAPS", "T": "Território"}
        for r in registros:
            label = local_labels.get(r.local_realizacao or "C", r.local_realizacao or "C")
            local_counts[label] += r.quantity or 1

        # ── Atendimentos por dia da semana ──
        weekday_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        weekday_counts = [0] * 7
        for r in registros:
            try:
                d = datetime.strptime(r.service_date, "%Y-%m-%d")
                weekday_counts[d.weekday()] += r.quantity or 1
            except (ValueError, TypeError):
                pass
        weekday_data = [{"day": weekday_labels[i], "count": weekday_counts[i]} for i in range(7)]

        # ── Média de atendimentos por paciente ──
        avg_per_patient = round(total_atendimentos / pacientes_ativos, 1) if pacientes_ativos > 0 else 0

        return {
            "stats": RelatorioService.get_dashboard_stats(db),
            "total_atendimentos": total_atendimentos,
            "pacientes_ativos": pacientes_ativos,
            "novos_pacientes": new_patients,
            "avg_per_patient": avg_per_patient,
            "top_profissionais": top_profs,
            "top_procedimentos": top_procs,
            "monthly": monthly,
            "gender_distribution": dict(gender_counts),
            "age_groups": dict(age_groups),
            "top_cids": top_cids,
            "service_type_distribution": dict(service_type_counts),
            "local_distribution": dict(local_counts),
            "weekday_distribution": weekday_data,
            "filter_month": month,
        }


# ═════════════════════════════════════════════════════════════════════════════
# 2. ROTAS DA API REST  (relatorio/relatorio_router.py)
#    Endpoints sob /api/relatorios
# ═════════════════════════════════════════════════════════════════════════════
api_router = APIRouter(prefix="/api/relatorios", tags=["Relatórios"])


def _require_auth(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user_id


@api_router.get("/dashboard")
def dashboard_stats(request: Request, db: Session = Depends(get_db)):
    """Números-resumo para o dashboard (pacientes, profissionais, etc.)."""
    _require_auth(request)
    return RelatorioService.get_dashboard_stats(db)


@api_router.get("/completo")
def relatorio_completo(request: Request, db: Session = Depends(get_db)):
    """Relatório completo com todos os indicadores e distribuições."""
    _require_auth(request)
    return RelatorioService.get_relatorio_completo(db)


# ═════════════════════════════════════════════════════════════════════════════
# 3. ROTA DA PÁGINA HTML  (relatorio/relatorio_frontend_router.py)
#    Renderiza a tela de Relatórios em /relatorios (com filtro por mês)
# ═════════════════════════════════════════════════════════════════════════════
frontend_router = APIRouter(tags=["Frontend - Relatórios"])


@frontend_router.get("/relatorios", response_class=HTMLResponse)
async def page_relatorios(request: Request, db: Session = Depends(get_db), month: str = None):
    # Autenticação
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    # Monta todos os indicadores (opcionalmente filtrados por competência)
    data = RelatorioService.get_relatorio_completo(db, month=month)

    return templates.TemplateResponse(request, "relatorios.html", {
        "user": user,
        "data": data,
        "active_page": "relatorios",
    })
