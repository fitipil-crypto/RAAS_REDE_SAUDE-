"""
Testes da exclusão em lote, incluindo a categoria "Registros do Mês Atual".
"""
from datetime import datetime

from paciente.paciente_service import PacienteService
from paciente.paciente_schema import PacienteCriar
from procedimento.procedimento_service import ProcedimentoService
from procedimento.procedimento_schema import ProcedimentoCriar
from registro.registro_service import RegistroService
from registro.registro_schema import RegistroCriar


def _seed_registro(db_session, service_month, service_date):
    paciente = PacienteService.criar(db_session, PacienteCriar(name=f"Paciente {service_month}"))
    procedimento = ProcedimentoService.criar(db_session, ProcedimentoCriar(
        code="0000000005", name="Procedimento Teste",
    ))
    return RegistroService.criar(db_session, RegistroCriar(
        service_month=service_month, service_date=service_date,
        patient_id=paciente.id, procedure_id=procedimento.id,
    ))


def test_deletar_por_mes_afeta_somente_o_mes_informado(db_session):
    mes_atual = datetime.now().strftime("%Y-%m")
    _seed_registro(db_session, mes_atual, f"{mes_atual}-10")
    _seed_registro(db_session, "2020-01", "2020-01-10")

    assert RegistroService.contar_por_mes(db_session, mes_atual) == 1

    removidos = RegistroService.deletar_por_mes(db_session, mes_atual)

    assert removidos == 1
    assert RegistroService.contar_por_mes(db_session, mes_atual) == 0
    assert RegistroService.contar_por_mes(db_session, "2020-01") == 1


def test_excluir_registros_mes_atual_via_api(db_session, auth_client):
    mes_atual = datetime.now().strftime("%Y-%m")
    _seed_registro(db_session, mes_atual, f"{mes_atual}-05")
    _seed_registro(db_session, "2020-01", "2020-01-05")

    resp = auth_client.post("/api/excluir", json={
        "tables": ["registros_mes_atual"], "confirm": "EXCLUIR",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["results"]["registros_mes_atual"] == 1
    assert RegistroService.contar_por_mes(db_session, mes_atual) == 0
    assert RegistroService.contar_por_mes(db_session, "2020-01") == 1


def test_excluir_registros_mes_atual_exige_confirmacao(auth_client):
    resp = auth_client.post("/api/excluir", json={
        "tables": ["registros_mes_atual"], "confirm": "errado",
    })
    assert resp.status_code == 400
