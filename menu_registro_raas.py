"""
═══════════════════════════════════════════════════════════════════════════════
MENU "NOVO REGISTRO RAAS" — Extração consolidada em Python
═══════════════════════════════════════════════════════════════════════════════

Este arquivo reúne, num único lugar, todo o código Python que compõe o menu
"Registros RAAS" do projeto saude_raas (FastAPI + SQLAlchemy + Pydantic).

No projeto original, este código está distribuído em 5 arquivos:
    registro/registro_model.py            → Modelo (tabela do banco)
    registro/registro_schema.py           → Schemas Pydantic (validação)
    registro/registro_service.py          → Regras de negócio / acesso a dados
    registro/registro_router.py           → Rotas da API REST (/api/registros)
    registro/registro_frontend_router.py  → Rota da página HTML (/registros)

Mais constantes auxiliares de  sistema/reference_data.py.

Um "Registro RAAS" representa um atendimento: cruza paciente × procedimento ×
profissional numa competência (mês), com serviço, classificação, equipe,
local de realização e quantidade.
"""

import uuid as uuid_lib
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse


# ═════════════════════════════════════════════════════════════════════════════
# 1. CONSTANTES AUXILIARES  (sistema/reference_data.py)
#    Opções de Serviço, Classificação e Tipo de Atendimento usadas no formulário.
# ═════════════════════════════════════════════════════════════════════════════
SERVICE_TYPE_MAP = {"01": "Individual", "02": "Grupo", "03": "Família"}

# Serviço (campo ras_srv) — padrão 115
SRV_OPTS = [
    {"value": "115", "label": "115 — Serviço de Atenção Psicossocial"},
    {"value": "116", "label": "116 — Serviço de Atenção à Saúde Mental"},
    {"value": "101", "label": "101 — Serviço de Apoio Diagnóstico e Terapia"},
    {"value": "136", "label": "136 — Serviço de Atenção em Saúde"},
]

# Classificação (campo ras_class) — padrão 002
CLS_OPTS = [
    {"value": "002", "label": "002 — Atendimento Psicossocial"},
    {"value": "003", "label": "003 — Atendimento de Saúde Mental"},
    {"value": "001", "label": "001 — Atenção Básica"},
    {"value": "004", "label": "004 — Serviço Especializado"},
]


# ═════════════════════════════════════════════════════════════════════════════
# 2. MODELO  (registro/registro_model.py)
#    Define a tabela "registros_raas" no banco de dados.
# ═════════════════════════════════════════════════════════════════════════════
# from database import Base   # no projeto real, Base vem de database.py
from database import Base  # noqa: E402


class Registro(Base):
    __tablename__ = "registros_raas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    service_month = Column(String(7), nullable=False, index=True)        # YYYY-MM (competência)
    service_date = Column(String(10), nullable=False)                    # YYYY-MM-DD (data do atendimento)
    patient_id = Column(String(36), nullable=False, index=True)          # FK paciente
    professional_id = Column(String(36), nullable=True, index=True)      # FK profissional executante
    procedure_id = Column(String(36), nullable=False, index=True)        # FK procedimento (SIGTAP)
    cbo_code = Column(String(10), nullable=True)                         # CBO do executante
    service_type = Column(String(2), nullable=True, default="01")        # 01=Individual, 02=Grupo, 03=Família
    local_realizacao = Column(String(1), nullable=True, default="C")     # C=CAPS, T=Território
    authorization = Column(String(20), nullable=True)                    # nº de autorização
    srv = Column(String(3), nullable=True, default="115")                # serviço (ras_srv)
    cls = Column(String(3), nullable=True, default="002")                # classificação (ras_class)
    team_code = Column(String(10), nullable=True)                        # código da equipe (INE)
    team_type = Column(String(3), nullable=True)                         # tipo de equipe
    quantity = Column(Integer, nullable=False, default=1)                # quantidade realizada
    notes = Column(Text, nullable=True)                                  # observações
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Registro(month='{self.service_month}', patient='{self.patient_id}')>"


# ═════════════════════════════════════════════════════════════════════════════
# 3. SCHEMAS PYDANTIC  (registro/registro_schema.py)
#    Validação de entrada/saída da API.
# ═════════════════════════════════════════════════════════════════════════════
class RegistroBase(BaseModel):
    service_month: str = Field(..., description="Competência YYYY-MM")
    service_date: str = Field(..., description="Data do atendimento YYYY-MM-DD")
    patient_id: str = Field(..., description="ID do paciente")
    professional_id: Optional[str] = None
    procedure_id: str = Field(..., description="ID do procedimento")
    cbo_code: Optional[str] = None
    service_type: str = Field(default="01")
    local_realizacao: str = Field(default="C")
    authorization: Optional[str] = None
    srv: str = Field(default="115")
    cls: str = Field(default="002")
    team_code: Optional[str] = None
    team_type: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class RegistroCriar(RegistroBase):
    """Payload para criar um registro."""
    pass


class RegistroAtualizar(BaseModel):
    """Payload para atualizar (todos os campos opcionais)."""
    service_month: Optional[str] = None
    service_date: Optional[str] = None
    patient_id: Optional[str] = None
    professional_id: Optional[str] = None
    procedure_id: Optional[str] = None
    cbo_code: Optional[str] = None
    service_type: Optional[str] = None
    local_realizacao: Optional[str] = None
    authorization: Optional[str] = None
    srv: Optional[str] = None
    cls: Optional[str] = None
    team_code: Optional[str] = None
    team_type: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None


class RegistroResposta(RegistroBase):
    """Resposta da API (inclui id e timestamps)."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ═════════════════════════════════════════════════════════════════════════════
# 4. SERVIÇO  (registro/registro_service.py)
#    Toda a lógica de negócio e acesso ao banco.
# ═════════════════════════════════════════════════════════════════════════════
class RegistroService:

    @staticmethod
    def listar_todos(db: Session, month: str = None) -> list[Registro]:
        query = db.query(Registro)
        if month:
            query = query.filter(Registro.service_month == month)
        return query.order_by(Registro.service_date.desc()).all()

    @staticmethod
    def obter_por_id(db: Session, registro_id: str) -> Registro | None:
        return db.query(Registro).filter(Registro.id == registro_id).first()

    @staticmethod
    def listar_por_mes(db: Session, month: str) -> list[Registro]:
        return (
            db.query(Registro)
            .filter(Registro.service_month == month)
            .order_by(Registro.service_date.desc())
            .all()
        )

    @staticmethod
    def listar_por_paciente(db: Session, patient_id: str) -> list[Registro]:
        return (
            db.query(Registro)
            .filter(Registro.patient_id == patient_id)
            .order_by(Registro.service_date.desc())
            .all()
        )

    @staticmethod
    def criar(db: Session, data: RegistroCriar) -> Registro:
        reg = Registro(id=str(uuid_lib.uuid4()), **data.model_dump())
        db.add(reg)
        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def criar_varios(db: Session, registros: list[RegistroCriar]) -> list[Registro]:
        """Cria vários registros de uma vez (até 5 procedimentos por atendimento)."""
        result = []
        for data in registros:
            reg = Registro(id=str(uuid_lib.uuid4()), **data.model_dump())
            db.add(reg)
            result.append(reg)
        db.commit()
        for r in result:
            db.refresh(r)
        return result

    @staticmethod
    def atualizar(db: Session, registro_id: str, data: RegistroAtualizar) -> Registro | None:
        reg = RegistroService.obter_por_id(db, registro_id)
        if not reg:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reg, key, value)
        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def deletar(db: Session, registro_id: str) -> bool:
        reg = RegistroService.obter_por_id(db, registro_id)
        if not reg:
            return False
        db.delete(reg)
        db.commit()
        return True

    @staticmethod
    def deletar_varios(db: Session, ids: list[str]) -> int:
        count = 0
        for rid in ids:
            if RegistroService.deletar(db, rid):
                count += 1
        return count

    @staticmethod
    def deletar_todos(db: Session) -> int:
        count = db.query(Registro).count()
        db.query(Registro).delete()
        db.commit()
        return count


# ═════════════════════════════════════════════════════════════════════════════
# 5. ROTAS DA API REST  (registro/registro_router.py)
#    Endpoints sob /api/registros
# ═════════════════════════════════════════════════════════════════════════════
from database import get_db  # noqa: E402

api_router = APIRouter(prefix="/api/registros", tags=["Registros RAAS"])


def _require_auth(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user_id


@api_router.get("/", response_model=List[RegistroResposta])
def listar_registros(request: Request, month: str = Query(None), db: Session = Depends(get_db)):
    _require_auth(request)
    return RegistroService.listar_todos(db, month)


@api_router.get("/{registro_id}", response_model=RegistroResposta)
def obter_registro(registro_id: str, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    reg = RegistroService.obter_por_id(db, registro_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return reg


@api_router.post("/", response_model=RegistroResposta)
def criar_registro(data: RegistroCriar, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    return RegistroService.criar(db, data)


@api_router.post("/varios", response_model=List[RegistroResposta])
def criar_varios_registros(registros: List[RegistroCriar], request: Request, db: Session = Depends(get_db)):
    """Cria vários procedimentos de um mesmo atendimento de uma vez (até 5 linhas)."""
    _require_auth(request)
    return RegistroService.criar_varios(db, registros)


@api_router.put("/{registro_id}", response_model=RegistroResposta)
def atualizar_registro(registro_id: str, data: RegistroAtualizar, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    reg = RegistroService.atualizar(db, registro_id, data)
    if not reg:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return reg


@api_router.delete("/{registro_id}")
def deletar_registro(registro_id: str, request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    success = RegistroService.deletar(db, registro_id)
    if not success:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return {"mensagem": "Registro excluído com sucesso"}


@api_router.post("/deletar-varios")
def deletar_varios(ids: List[str], request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    count = RegistroService.deletar_varios(db, ids)
    return {"mensagem": f"{count} registro(s) excluído(s)"}


# ═════════════════════════════════════════════════════════════════════════════
# 6. ROTA DA PÁGINA HTML  (registro/registro_frontend_router.py)
#    Renderiza o menu "Novo Registro RAAS" em /registros
# ═════════════════════════════════════════════════════════════════════════════
from usuario.usuario_service import UsuarioService                                  # noqa: E402
from paciente.paciente_service import PacienteService                               # noqa: E402
from profissional.profissional_service import ProfissionalService                   # noqa: E402
from procedimento.procedimento_service import ProcedimentoService, get_sigtap_name  # noqa: E402

frontend_router = APIRouter(tags=["Frontend - Registros"])


@frontend_router.get("/registros", response_class=HTMLResponse)
async def page_registros(request: Request, month: str = Query(None), db: Session = Depends(get_db)):
    # Autenticação
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    # Competência padrão = mês atual
    if not month:
        month = datetime.now().strftime("%Y-%m")

    # Carrega registros da competência + entidades relacionadas
    registros = RegistroService.listar_por_mes(db, month)
    pacientes = {p.id: p for p in PacienteService.listar_todos(db)}
    profissionais = {p.id: p for p in ProfissionalService.listar_todos(db)}
    procedimentos = {p.id: p for p in ProcedimentoService.listar_todos(db)}

    # Enriquece cada registro com nomes para exibição
    for r in registros:
        proc = procedimentos.get(r.procedure_id)
        r.procedure_name = (get_sigtap_name(proc.code) if proc else None) or (proc.name if proc else "—")
        r.professional_name = profissionais.get(r.professional_id).name if profissionais.get(r.professional_id) else "—"
        r.service_type_label = SERVICE_TYPE_MAP.get(r.service_type, "—")

    # Agrupa por paciente (cada atendimento mostra o paciente + seus procedimentos)
    grouped = defaultdict(list)
    for r in registros:
        grouped[r.patient_id].append(r)
    groups = []
    for pid, recs in grouped.items():
        pat = pacientes.get(pid)
        groups.append({"patient": pat, "records": recs})

    # Profissionais e procedimentos ativos para preencher o formulário
    active_professionals = [p for p in profissionais.values() if p.active]
    active_procedures = []
    for p in procedimentos.values():
        if p.active:
            # Rótulo amigável: "código — nome oficial SIGTAP"
            p.label = f"{p.code} — {get_sigtap_name(p.code) or p.name}"
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
        "srv_opts": SRV_OPTS,        # opções de Serviço (padrão 115)
        "cls_opts": CLS_OPTS,        # opções de Classificação (padrão 002)
        "service_type_map": SERVICE_TYPE_MAP,
        "active_page": "registros",
    })
