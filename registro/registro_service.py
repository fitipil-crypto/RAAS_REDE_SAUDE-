"""
Serviço para gerenciamento de registros RAAS.
"""
import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from registro.registro_model import Registro
from registro.registro_schema import RegistroCriar, RegistroAtualizar


class RegistroService:

    @staticmethod
    def listar_todos(db: Session, month: str = None) -> list[Registro]:
        query = db.query(Registro)
        if month:
            query = query.filter(Registro.service_month == month)
        return query.order_by(Registro.service_date.desc()).all()

    @staticmethod
    def contar_todos(db: Session) -> int:
        return db.query(func.count(Registro.id)).scalar() or 0

    @staticmethod
    def estatisticas_mes(db: Session, month: str) -> dict:
        """Contagens agregadas (via SQL, sem carregar os registros) para o dashboard."""
        base = db.query(Registro).filter(Registro.service_month == month)
        return {
            "registros": base.with_entities(func.count(Registro.id)).scalar() or 0,
            "pacientes": base.with_entities(func.count(func.distinct(Registro.patient_id))).scalar() or 0,
            "procedimentos": base.with_entities(func.count(func.distinct(Registro.procedure_id))).scalar() or 0,
        }

    @staticmethod
    def contagem_por_dia(db: Session, data_inicio: str) -> dict[str, int]:
        """Quantidade de registros por service_date, a partir de data_inicio (YYYY-MM-DD)."""
        linhas = (
            db.query(Registro.service_date, func.count(Registro.id))
            .filter(Registro.service_date >= data_inicio)
            .group_by(Registro.service_date)
            .all()
        )
        return dict(linhas)

    @staticmethod
    def obter_por_id(db: Session, registro_id: str) -> Registro | None:
        return db.query(Registro).filter(Registro.id == registro_id).first()

    @staticmethod
    def listar_por_mes(db: Session, month: str) -> list[Registro]:
        return db.query(Registro).filter(Registro.service_month == month).order_by(Registro.service_date.desc()).all()

    @staticmethod
    def listar_por_paciente(db: Session, patient_id: str) -> list[Registro]:
        return db.query(Registro).filter(Registro.patient_id == patient_id).order_by(Registro.service_date.desc()).all()

    @staticmethod
    def criar(db: Session, data: RegistroCriar) -> Registro:
        reg = Registro(
            id=str(uuid_lib.uuid4()),
            **data.model_dump()
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def criar_varios(db: Session, registros: list[RegistroCriar]) -> list[Registro]:
        result = []
        for data in registros:
            reg = Registro(
                id=str(uuid_lib.uuid4()),
                **data.model_dump()
            )
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

    @staticmethod
    def contar_por_mes(db: Session, month: str) -> int:
        return db.query(func.count(Registro.id)).filter(Registro.service_month == month).scalar() or 0

    @staticmethod
    def deletar_por_mes(db: Session, month: str) -> int:
        count = db.query(Registro).filter(Registro.service_month == month).count()
        db.query(Registro).filter(Registro.service_month == month).delete()
        db.commit()
        return count
