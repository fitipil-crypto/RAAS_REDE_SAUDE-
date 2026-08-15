"""
Testes do cálculo do campo de controle (SMT-VRF) na exportação RAAS.

Algoritmo (fornecido pelo usuário):
1) Soma do código de cada procedimento + quantidade da linha (Registro 16)
2) Soma do código CNES + CNS do paciente de cada linha (Registro 15)
3) Soma dos dois subtotais
4) Resto da divisão do resultado por 1111
5) 1111 + resto  →  campo de controle (domínio 1111..2221)
"""
from exportacao.exportacao_service import ExportacaoService, _calcular_campo_controle, _digits_int
from paciente.paciente_service import PacienteService
from paciente.paciente_schema import PacienteCriar
from procedimento.procedimento_service import ProcedimentoService
from procedimento.procedimento_schema import ProcedimentoCriar
from registro.registro_service import RegistroService
from registro.registro_schema import RegistroCriar


def test_calcular_campo_controle_formula():
    # soma16 = 5 (procedimento) + 3 (quantidade) = 8
    # soma15 = 1 (CNES) + 2 (CNS) = 3
    # total = 11 -> resto de 11 % 1111 = 11 -> 1111 + 11 = 1122
    assert _calcular_campo_controle(soma16=8, soma15=3) == "1122"


def test_calcular_campo_controle_dominio():
    # o resultado deve sempre cair no domínio 1111..2221
    for soma16, soma15 in [(0, 0), (10**9, 10**9), (1110, 0), (1111, 0)]:
        valor = int(_calcular_campo_controle(soma16, soma15))
        assert 1111 <= valor <= 2221


def test_digits_int():
    assert _digits_int("03.01.08.019-4") == 301080194
    assert _digits_int("0000000005") == 5
    assert _digits_int(None) == 0
    assert _digits_int("") == 0


def test_exportar_raas_campo_controle_no_cabecalho(db_session):
    paciente = PacienteService.criar(db_session, PacienteCriar(
        name="Paciente Teste", cns="2",
    ))
    procedimento = ProcedimentoService.criar(db_session, ProcedimentoCriar(
        code="0000000005", name="Procedimento Teste",
    ))
    RegistroService.criar(db_session, RegistroCriar(
        service_month="2026-07", service_date="2026-07-10",
        patient_id=paciente.id, procedure_id=procedimento.id,
        quantity=3,
    ))

    content, filename, total = ExportacaoService.exportar_raas(
        db_session, "2026-07", header_overrides={"cnes_code": "0000001"},
    )

    assert total == 1
    header = content.split("\r\n")[0]
    campo_controle = header[19:23]  # posições 20-23 (1-based)

    # soma16 = 5 + 3 = 8 · soma15 = 1 (CNES) + 2 (CNS) = 3 · total = 11 · resto = 11 · 1111+11 = 1122
    assert campo_controle == "1122"
