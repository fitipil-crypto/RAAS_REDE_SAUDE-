"""
Modelo de dados para pacientes.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.sql import func
from database import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))

    # Identificação
    name = Column(String(200), nullable=False)
    prontuario = Column(String(50), nullable=True)
    cns = Column(String(20), nullable=True, index=True)
    cpf = Column(String(14), nullable=True, index=True)
    birth_date = Column(String(10), nullable=True)
    nationality = Column(String(10), nullable=True, default="010")
    gender = Column(String(1), nullable=True)
    race = Column(String(2), nullable=True)
    ethnicity = Column(String(50), nullable=True)
    carate = Column(String(2), nullable=True)
    street_code = Column(String(10), nullable=True)
    mot_saida = Column(String(2), nullable=True)
    mother_name = Column(String(200), nullable=True)
    guardian_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    cell_phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

    # Endereço
    cep = Column(String(10), nullable=True)
    street_type = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    street_number = Column(String(10), nullable=True)
    address_complement = Column(String(50), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    municipality_code = Column(String(10), nullable=True)

    # Clínico / Social
    admission_date = Column(String(10), nullable=True)
    user_origin = Column(String(2), nullable=True, default="01")
    cid_main = Column(String(10), nullable=True)
    cid_associated1 = Column(String(10), nullable=True)
    cid_associated2 = Column(String(10), nullable=True)
    cid_causes = Column(String(10), nullable=True)
    esf_coverage = Column(String(1), nullable=True, default="N")
    cnes_usf = Column(String(10), nullable=True)
    user_destination = Column(String(2), nullable=True, default="00")
    conclusion_date = Column(String(10), nullable=True)
    street_situation = Column(String(1), nullable=True, default="N")
    drug_user = Column(String(1), nullable=True, default="N")
    alcohol_user = Column(Boolean, default=False)
    crack_user = Column(Boolean, default=False)
    other_drugs_user = Column(Boolean, default=False)
    authorization_number = Column(String(20), nullable=True)

    # Validação
    date_ini_valid = Column(String(10), nullable=True)
    date_fim_valid = Column(String(10), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Paciente(name='{self.name}', cns='{self.cns}')>"
