"""
Serviço para gerenciamento de pacientes.
"""
import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy import or_

from paciente.paciente_model import Paciente
from paciente.paciente_schema import PacienteCriar, PacienteAtualizar


class PacienteService:

    @staticmethod
    def listar_todos(db: Session, search: str = None) -> list[Paciente]:
        query = db.query(Paciente)
        if search:
            q = f"%{search}%"
            query = query.filter(
                or_(
                    Paciente.name.ilike(q),
                    Paciente.cns.ilike(q),
                    Paciente.cpf.ilike(q),
                    Paciente.prontuario.ilike(q),
                )
            )
        return query.order_by(Paciente.name.asc()).all()

    @staticmethod
    def contar_todos(db: Session) -> int:
        return db.query(Paciente).count()

    @staticmethod
    def obter_por_id(db: Session, paciente_id: str) -> Paciente | None:
        return db.query(Paciente).filter(Paciente.id == paciente_id).first()

    @staticmethod
    def obter_por_cns(db: Session, cns: str) -> Paciente | None:
        return db.query(Paciente).filter(Paciente.cns == cns).first()

    @staticmethod
    def obter_por_cpf(db: Session, cpf: str) -> Paciente | None:
        return db.query(Paciente).filter(Paciente.cpf == cpf).first()

    @staticmethod
    def criar(db: Session, data: PacienteCriar) -> Paciente:
        paciente = Paciente(
            id=str(uuid_lib.uuid4()),
            **data.model_dump()
        )
        db.add(paciente)
        db.commit()
        db.refresh(paciente)
        return paciente

    @staticmethod
    def atualizar(db: Session, paciente_id: str, data: PacienteAtualizar) -> Paciente | None:
        paciente = PacienteService.obter_por_id(db, paciente_id)
        if not paciente:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(paciente, key, value)
        db.commit()
        db.refresh(paciente)
        return paciente

    @staticmethod
    def deletar(db: Session, paciente_id: str) -> bool:
        paciente = PacienteService.obter_por_id(db, paciente_id)
        if not paciente:
            return False
        db.delete(paciente)
        db.commit()
        return True

    @staticmethod
    def deletar_varios(db: Session, ids: list[str]) -> int:
        count = 0
        for pid in ids:
            if PacienteService.deletar(db, pid):
                count += 1
        return count

    @staticmethod
    def deletar_todos(db: Session) -> int:
        count = db.query(Paciente).count()
        db.query(Paciente).delete()
        db.commit()
        return count
