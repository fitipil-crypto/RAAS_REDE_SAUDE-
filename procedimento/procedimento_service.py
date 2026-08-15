"""
Serviço para gerenciamento de procedimentos.
"""
import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy import or_

from procedimento.procedimento_model import Procedimento
from procedimento.procedimento_schema import ProcedimentoCriar, ProcedimentoAtualizar


SIGTAP_NAMES = {
    "03.01.08.019-4": "Atenção/Acompanhamento de Paciente em Sofrimento Psíquico em Situação de Risco",
    "03.01.08.020-8": "Atenção/Acompanhamento de Pessoa com Transtorno Mental",
    "03.01.08.021-6": "Atenção/Acompanhamento de Criança com Transtorno Mental",
    "03.01.08.022-4": "Atenção/Acompanhamento de Adolescente com Transtorno Mental",
    "03.01.08.024-0": "Atenção/Acompanhamento de Pessoa com Transtorno por Uso de Álcool e Outras Drogas",
    "03.01.08.027-5": "Atenção/Acompanhamento em Grupo de Paciente com Transtorno Mental",
    "03.01.08.028-3": "Atenção/Acompanhamento de Pessoa com Transtorno Mental em Oficina Terapêutica",
    "03.01.08.029-1": "Atenção/Acompanhamento de Pessoa com Transtorno Mental em Atividade de Reabilitação Psicossocial",
    "03.01.08.034-8": "Visita Domiciliar a Familiar de Pessoa com Transtorno Mental",
    "03.01.08.035-6": "Visita Domiciliar a Pessoa com Transtorno Mental",
    "0301080194": "Atenção/Acompanhamento de Paciente em Sofrimento Psíquico em Situação de Risco",
    "0301080208": "Atenção/Acompanhamento de Pessoa com Transtorno Mental",
    "0301080216": "Atenção/Acompanhamento de Criança com Transtorno Mental",
    "0301080224": "Atenção/Acompanhamento de Adolescente com Transtorno Mental",
    "0301080240": "Atenção/Acompanhamento de Pessoa com Transtorno por Uso de Álcool e Outras Drogas",
    "0301080275": "Atenção/Acompanhamento em Grupo de Paciente com Transtorno Mental",
    "0301080283": "Atenção/Acompanhamento de Pessoa com Transtorno Mental em Oficina Terapêutica",
    "0301080291": "Atenção/Acompanhamento de Pessoa com Transtorno Mental em Atividade de Reabilitação Psicossocial",
    "0301080348": "Visita Domiciliar a Familiar de Pessoa com Transtorno Mental",
    "0301080356": "Visita Domiciliar a Pessoa com Transtorno Mental",
}


def get_sigtap_name(raw_or_fmt: str) -> str | None:
    if not raw_or_fmt:
        return None
    if raw_or_fmt in SIGTAP_NAMES:
        return SIGTAP_NAMES[raw_or_fmt]
    raw = "".join(c for c in raw_or_fmt if c.isdigit()).zfill(10)
    if raw in SIGTAP_NAMES:
        return SIGTAP_NAMES[raw]
    fmt = f"{raw[:2]}.{raw[2:4]}.{raw[4:6]}.{raw[6:9]}-{raw[9]}" if len(raw) == 10 else raw_or_fmt
    if fmt in SIGTAP_NAMES:
        return SIGTAP_NAMES[fmt]
    return None


def fmt_sigtap(raw: str) -> str:
    d = "".join(c for c in (raw or "") if c.isdigit()).zfill(10)
    return f"{d[:2]}.{d[2:4]}.{d[4:6]}.{d[6:9]}-{d[9]}"


class ProcedimentoService:

    @staticmethod
    def listar_todos(db: Session, search: str = None, ativos_only: bool = False) -> list[Procedimento]:
        query = db.query(Procedimento)
        if ativos_only:
            query = query.filter(Procedimento.active == True)
        if search:
            q = f"%{search}%"
            query = query.filter(
                or_(
                    Procedimento.name.ilike(q),
                    Procedimento.code.ilike(q),
                )
            )
        return query.order_by(Procedimento.name.asc()).all()

    @staticmethod
    def contar_todos(db: Session) -> int:
        return db.query(Procedimento).count()

    @staticmethod
    def obter_por_id(db: Session, procedimento_id: str) -> Procedimento | None:
        return db.query(Procedimento).filter(Procedimento.id == procedimento_id).first()

    @staticmethod
    def obter_por_code(db: Session, code: str) -> Procedimento | None:
        return db.query(Procedimento).filter(Procedimento.code == code).first()

    @staticmethod
    def criar(db: Session, data: ProcedimentoCriar) -> Procedimento:
        proc = Procedimento(
            id=str(uuid_lib.uuid4()),
            **data.model_dump()
        )
        db.add(proc)
        db.commit()
        db.refresh(proc)
        return proc

    @staticmethod
    def atualizar(db: Session, procedimento_id: str, data: ProcedimentoAtualizar) -> Procedimento | None:
        proc = ProcedimentoService.obter_por_id(db, procedimento_id)
        if not proc:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(proc, key, value)
        db.commit()
        db.refresh(proc)
        return proc

    @staticmethod
    def deletar(db: Session, procedimento_id: str) -> bool:
        proc = ProcedimentoService.obter_por_id(db, procedimento_id)
        if not proc:
            return False
        db.delete(proc)
        db.commit()
        return True

    @staticmethod
    def deletar_varios(db: Session, ids: list[str]) -> int:
        count = 0
        for pid in ids:
            if ProcedimentoService.deletar(db, pid):
                count += 1
        return count

    @staticmethod
    def deletar_todos(db: Session) -> int:
        count = db.query(Procedimento).count()
        db.query(Procedimento).delete()
        db.commit()
        return count
