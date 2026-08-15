"""
Serviço para gerenciamento de profissionais.
"""
import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy import or_

from profissional.profissional_model import Profissional
from profissional.profissional_schema import ProfissionalCriar, ProfissionalAtualizar


class ProfissionalService:

    @staticmethod
    def listar_todos(db: Session, search: str = None, ativos_only: bool = False) -> list[Profissional]:
        query = db.query(Profissional)
        if ativos_only:
            query = query.filter(Profissional.active == True)
        if search:
            q = f"%{search}%"
            query = query.filter(
                or_(
                    Profissional.name.ilike(q),
                    Profissional.cns.ilike(q),
                    Profissional.specialty.ilike(q),
                )
            )
        return query.order_by(Profissional.name.asc()).all()

    @staticmethod
    def contar_todos(db: Session) -> int:
        return db.query(Profissional).count()

    @staticmethod
    def obter_por_id(db: Session, profissional_id: str) -> Profissional | None:
        return db.query(Profissional).filter(Profissional.id == profissional_id).first()

    @staticmethod
    def obter_por_cns(db: Session, cns: str) -> Profissional | None:
        return db.query(Profissional).filter(Profissional.cns == cns).first()

    @staticmethod
    def obter_por_cpf(db: Session, cpf: str) -> Profissional | None:
        return db.query(Profissional).filter(Profissional.cpf == cpf).first()

    @staticmethod
    def obter_por_nome(db: Session, name: str) -> Profissional | None:
        return db.query(Profissional).filter(Profissional.name == name).first()

    @staticmethod
    def criar(db: Session, data: ProfissionalCriar) -> Profissional:
        prof = Profissional(
            id=str(uuid_lib.uuid4()),
            **data.model_dump()
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)
        return prof

    @staticmethod
    def atualizar(db: Session, profissional_id: str, data: ProfissionalAtualizar) -> Profissional | None:
        prof = ProfissionalService.obter_por_id(db, profissional_id)
        if not prof:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(prof, key, value)
        db.commit()
        db.refresh(prof)
        return prof

    @staticmethod
    def deletar(db: Session, profissional_id: str) -> bool:
        prof = ProfissionalService.obter_por_id(db, profissional_id)
        if not prof:
            return False
        db.delete(prof)
        db.commit()
        return True

    @staticmethod
    def deletar_varios(db: Session, ids: list[str]) -> int:
        count = 0
        for pid in ids:
            if ProfissionalService.deletar(db, pid):
                count += 1
        return count

    @staticmethod
    def deletar_todos(db: Session) -> int:
        count = db.query(Profissional).count()
        db.query(Profissional).delete()
        db.commit()
        return count
