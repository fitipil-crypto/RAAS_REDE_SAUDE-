"""
Serviço para exportação de arquivos RAAS.

Gera o arquivo posicional fixo (padrão SIA/RAAS DATASUS) com registros
01 (cabeçalho), 15 (paciente/atendimento) e 16 (procedimento).
Também gera CSV para análise.

Para ajustar posições/tamanhos do layout, edite as funções build_* abaixo.
"""
import csv
import io
import re
from datetime import datetime
from sqlalchemy.orm import Session

from registro.registro_service import RegistroService
from paciente.paciente_service import PacienteService
from profissional.profissional_service import ProfissionalService
from procedimento.procedimento_service import ProcedimentoService
from config.config_service import ConfigService
from sistema.reference_data import (
    sanitize, only_digits, fmt_sigtap, get_sigtap_name, SERVICE_TYPE_MAP,
)


def _pad_l(v, n, c="0"):
    return str(v or "").rjust(n, c)[:n] if len(str(v or "")) <= n else str(v or "")[:n]


def _pad_l_strict(v, n, c="0"):
    s = str(v or "")
    return s.rjust(n, c)[-n:] if len(s) > n else s.rjust(n, c)


def _pad_r(v, n, c=" "):
    return str(v or "").ljust(n, c)[:n]


def _fmt_d(d):
    """yyyy-mm-dd → YYYYMMDD; vazio → 00000000"""
    if not d:
        return "00000000"
    s = re.sub(r"\D", "", str(d))
    if len(s) >= 8:
        return s[:8]
    return s.ljust(8, "0")


def _fmt_d_blank(d):
    """yyyy-mm-dd → YYYYMMDD; vazio → espaços em branco (campo opcional)."""
    if not d:
        return " " * 8
    return _fmt_d(d)


class _Line:
    """Buffer posicional 1-based. put(ini, fim, valor, align) escreve o campo
    exatamente nas colunas [ini..fim] (inclusivas), garantindo que o writer
    case com as posições lidas pelo parser de importação."""
    def __init__(self, size):
        self.buf = [" "] * size
        self.size = size

    def put(self, ini, fim, value, align="l", fill=" "):
        width = fim - ini + 1
        s = str(value if value is not None else "")
        if align == "r":
            s = s.rjust(width, fill)[-width:] if len(s) > width else s.rjust(width, fill)
        else:
            s = s.ljust(width, fill)[:width]
        for i, ch in enumerate(s):
            self.buf[ini - 1 + i] = ch
        return self

    def __str__(self):
        return "".join(self.buf)


def _pad_num_or_blank(v, n):
    """Zero-preenchido à direita quando há valor; espaços em branco quando vazio."""
    d = only_digits(v)
    if not d:
        return " " * n
    return _pad_l_strict(d, n, "r", "0")


def _digits_int(s):
    d = only_digits(s or "")
    return int(d) if d else 0


def _calcular_campo_controle(soma16: int, soma15: int) -> str:
    """Campo de controle do cabeçalho (SMT-VRF), domínio 1111..2221:
    1) soma do código de cada procedimento + quantidade da linha (Registro 16)
    2) soma do código CNES + CNS do paciente de cada linha (Registro 15)
    3) soma dos dois subtotais
    4) resto da divisão do resultado por 1111
    5) 1111 + resto
    """
    resto = (soma16 + soma15) % 1111
    return str(1111 + resto)


def _build_header(config, comp, n_proc, campo_controle):
    """Registro 01 — cabeçalho (144 posições)."""
    uf = _pad_l_strict(config.get("uf_code", "35"), 2)
    cnes = _pad_l_strict(config.get("cnes_code", "0000000"), 7)
    dt_ger = datetime.now().strftime("%Y%m%d")
    # Versão BDSIA é editável; usa padrão se vazia
    bdversao = (config.get("bdversao") or "").strip()
    bdversao = bdversao if bdversao else (comp + "a")
    L = _Line(144)
    L.put(1, 2, "01")
    L.put(3, 7, "#RAS#")
    L.put(8, 13, comp)
    L.put(14, 19, str(n_proc), "r", "0")
    L.put(20, 23, campo_controle)
    L.put(24, 53, sanitize(config.get("organ_name", "CAPS")))
    L.put(54, 59, sanitize(config.get("organ_code", "CAPS01")))
    L.put(60, 73, _pad_l_strict(only_digits(config.get("cnpj", "")), 14), "r", "0")
    L.put(74, 113, sanitize(config.get("destination_organ", "SECRETARIA MUNICIPAL DE SAUDE")))
    L.put(114, 114, config.get("destination_indicator", "M"))
    L.put(115, 122, dt_ger)
    L.put(123, 127, config.get("versao", "02.31"))
    L.put(138, 144, bdversao)
    return str(L)


def _build_r15(pat, uf, cnes, comp, dt_ini, dt_fim, n_acoes):
    """Registro 15 — paciente (406 posições). 1 por paciente."""
    gender = "F" if (pat.gender if hasattr(pat, 'gender') else pat.get("gender")) == "F" else "M"
    race = _pad_l_strict((pat.race if hasattr(pat, 'race') else pat.get("race")) or "01", 2)
    tipo = ("A" if (pat.alcohol_user if hasattr(pat, 'alcohol_user') else pat.get("alcohol_user")) else "") + \
           ("C" if (pat.crack_user if hasattr(pat, 'crack_user') else pat.get("crack_user")) else "") + \
           ("O" if (pat.other_drugs_user if hasattr(pat, 'other_drugs_user') else pat.get("other_drugs_user")) else "")
    esf = ((pat.esf_coverage if hasattr(pat, 'esf_coverage') else pat.get("esf_coverage")) or "N")[:1]

    def _g(attr, default=""):
        return (getattr(pat, attr, None) if hasattr(pat, attr) else pat.get(attr)) or default

    L = _Line(406)
    L.put(1, 2, "15")
    L.put(3, 4, uf)
    L.put(5, 10, comp)
    L.put(11, 17, cnes)
    L.put(18, 32, _pad_l_strict(only_digits(_g("cns")), 15), "r", "0")
    L.put(33, 40, dt_ini)
    L.put(41, 48, dt_fim)
    L.put(49, 78, sanitize(_g("name")))
    L.put(79, 88, only_digits(_g("prontuario")))
    L.put(89, 118, sanitize(_g("mother_name")))
    L.put(119, 148, sanitize(_g("address")))
    L.put(149, 153, only_digits(_g("street_number")))
    L.put(154, 163, sanitize(_g("address_complement")))
    L.put(164, 171, _pad_l_strict(only_digits(_g("cep")), 8), "r", "0")
    L.put(172, 178, _g("municipality_code"))
    L.put(179, 186, _fmt_d(_g("birth_date")))
    L.put(187, 187, gender)
    L.put(188, 189, race)
    L.put(190, 219, sanitize(_g("guardian_name") or _g("name")))
    L.put(220, 222, _pad_l_strict(_g("nationality") or "010", 3), "r", "0")
    L.put(223, 226, _pad_num_or_blank(_g("ethnicity"), 4))
    L.put(227, 237, _g("phone"))
    L.put(238, 248, _g("cell_phone"))
    L.put(249, 250, _g("mot_saida", "21")[:2])
    L.put(251, 258, _fmt_d_blank(_g("conclusion_date")))
    L.put(259, 262, sanitize(_g("cid_main")))
    L.put(263, 266, sanitize(_g("cid_associated1")))
    L.put(267, 270, sanitize(_g("cid_associated2")))
    L.put(275, 278, sanitize(_g("cid_causes")))
    L.put(279, 280, sanitize(_g("carate")))
    L.put(281, 282, _g("user_origin", "01")[:2])
    L.put(283, 283, esf)
    L.put(284, 290, _pad_num_or_blank(_g("cnes_usf") if esf == "S" else "", 7))
    L.put(291, 295, str(n_acoes), "r", "0")
    L.put(296, 297, _g("user_destination", "00")[:2])
    L.put(298, 300, "RAS")
    L.put(301, 301, _g("street_situation", "N")[:1])
    L.put(302, 302, _g("drug_user", "N")[:1])
    L.put(303, 305, tipo)
    L.put(306, 318, sanitize(_g("authorization_number")))
    L.put(319, 348, sanitize(_g("neighborhood")))
    L.put(349, 351, sanitize(_g("street_code")))
    L.put(352, 391, sanitize(_g("email"))[:40])
    L.put(392, 402, _pad_l_strict(only_digits(_g("cpf")), 11), "r", "0")
    return str(L)


def _build_r16(rec, proc, prof, pat, uf, cnes, comp, dt_ini):
    """Registro 16 — procedimento/profissional (110 posições)."""
    def _g(obj, attr, default=""):
        return (getattr(obj, attr, None) if hasattr(obj, attr) else (obj or {}).get(attr)) or default

    proc_code = only_digits(_g(proc, "code")).rjust(10, "0")[:10]
    L = _Line(110)
    L.put(1, 2, "16")
    L.put(3, 4, uf)
    L.put(5, 10, comp)
    L.put(11, 17, cnes)
    L.put(18, 32, _pad_l_strict(only_digits(_g(pat, "cns")), 15), "r", "0")
    L.put(33, 40, dt_ini)
    L.put(41, 50, proc_code, "r", "0")
    L.put(51, 56, _pad_l_strict(_g(rec, "cbo_code") or _g(prof, "cbo"), 6), "r", "0")
    L.put(57, 71, _pad_l_strict(only_digits(_g(prof, "cns")), 15), "r", "0")
    L.put(72, 79, _fmt_d(_g(rec, "service_date")))
    L.put(80, 82, _pad_l_strict(_g(rec, "srv") or "115", 3), "r", "0")
    L.put(83, 85, _pad_l_strict(_g(rec, "cls") or "002", 3), "r", "0")
    L.put(86, 91, _pad_l_strict(_g(rec, "quantity") or 1, 6), "r", "0")
    L.put(92, 94, "RAS")
    L.put(95, 95, (_g(rec, "local_realizacao") or "C")[:1])
    L.put(96, 106, _pad_l_strict(only_digits(_g(pat, "cpf")), 11), "r", "0")
    return str(L)


class ExportacaoService:

    @staticmethod
    def exportar_raas(db: Session, month: str, file_suffix: str = "CAPSI1",
                      header_overrides: dict = None) -> tuple:
        """Gera arquivo RAAS no formato DATASUS (Registro 01, 15, 16).

        header_overrides: dict opcional com os campos editáveis do cabeçalho
        (Registro 01) informados na tela de exportação. Quando presentes,
        sobrescrevem os valores vindos das Configurações do estabelecimento.
        Chaves aceitas: uf_code, cnes_code, organ_name, organ_code, cnpj,
        destination_organ, destination_indicator, versao, bdversao.
        O campo de controle (posições 20-23 do cabeçalho) não é mais configurável:
        é sempre calculado a partir dos registros 15/16 do próprio arquivo
        (ver _calcular_campo_controle).

        Retorna (conteudo_texto, nome_arquivo, qtd_procedimentos)."""
        config = dict(ConfigService.get_config_estabelecimento(db) or {})
        if header_overrides:
            for k, v in header_overrides.items():
                if v is not None and str(v).strip() != "":
                    config[k] = v
        registros = RegistroService.listar_por_mes(db, month)
        if not registros:
            return None, None, 0

        pacientes = {p.id: p for p in PacienteService.listar_todos(db)}
        profissionais = {p.id: p for p in ProfissionalService.listar_todos(db)}
        procedimentos = {p.id: p for p in ProcedimentoService.listar_todos(db)}

        y, m = month.split("-")
        comp = f"{y}{m}"
        uf = _pad_l_strict(config.get("uf_code", "35"), 2)
        cnes = _pad_l_strict(config.get("cnes_code", "0000000"), 7)
        cnes_num = _digits_int(cnes)

        # Agrupa registros por paciente
        by_pat = {}
        for reg in registros:
            by_pat.setdefault(reg.patient_id, []).append(reg)

        corpo = []
        soma16 = 0
        soma15 = 0
        for pat_id, recs in by_pat.items():
            pat = pacientes.get(pat_id)
            if not pat:
                continue
            dt_ini = _fmt_d(getattr(pat, "date_ini_valid", None) or recs[0].service_date)
            dt_fim = _fmt_d_blank(getattr(pat, "date_fim_valid", None))
            corpo.append(_build_r15(pat, uf, cnes, comp, dt_ini, dt_fim, len(recs)))
            soma15 += cnes_num + _digits_int(getattr(pat, "cns", None))

            for rec in recs:
                proc = procedimentos.get(rec.procedure_id)
                prof = profissionais.get(rec.professional_id) if rec.professional_id else None
                corpo.append(_build_r16(rec, proc, prof, pat, uf, cnes, comp, dt_ini))
                soma16 += _digits_int(proc.code if proc else None) + (rec.quantity or 1)

        campo_controle = _calcular_campo_controle(soma16, soma15)
        lines = [_build_header(config, comp, len(registros), campo_controle)] + corpo

        content = "\r\n".join(lines) + "\r\n"
        suffix = (file_suffix or "")[:6]
        filename = "AA" + suffix.ljust(6, "_")
        return content, filename, len(registros)

    @staticmethod
    def exportar_csv(db: Session, month: str) -> tuple:
        """Gera arquivo CSV com os registros do mês.
        Retorna (conteudo_csv, nome_arquivo, qtd_registros)."""
        registros = RegistroService.listar_por_mes(db, month)
        if not registros:
            return None, None, 0

        pacientes = {p.id: p for p in PacienteService.listar_todos(db)}
        profissionais = {p.id: p for p in ProfissionalService.listar_todos(db)}
        procedimentos = {p.id: p for p in ProcedimentoService.listar_todos(db)}

        output = io.StringIO()
        output.write("\ufeff")  # BOM para Excel
        writer = csv.writer(output, delimiter=";")
        writer.writerow([
            "Data", "Paciente", "CNS Paciente", "Procedimento", "Codigo",
            "Profissional", "CNS Profissional", "CBO", "Tipo", "Quantidade",
        ])

        for reg in registros:
            pac = pacientes.get(reg.patient_id)
            prof = profissionais.get(reg.professional_id)
            proc = procedimentos.get(reg.procedure_id)
            writer.writerow([
                reg.service_date or "",
                pac.name if pac else "",
                pac.cns if pac else "",
                proc.name if proc else "",
                proc.code if proc else "",
                prof.name if prof else "",
                prof.cns if prof else "",
                reg.cbo_code or "",
                SERVICE_TYPE_MAP.get(reg.service_type, ""),
                reg.quantity or 1,
            ])

        return output.getvalue(), f"RAAS_{month}.csv", len(registros)

    @staticmethod
    def get_stats(db: Session, month: str) -> dict:
        """Estatísticas do mês para preview."""
        registros = RegistroService.listar_por_mes(db, month)
        pat_ids = set()
        prof_ids = set()
        proc_ids = set()
        for r in registros:
            pat_ids.add(r.patient_id)
            if r.professional_id:
                prof_ids.add(r.professional_id)
            proc_ids.add(r.procedure_id)

        return {
            "total_registros": len(registros),
            "total_pacientes": len(pat_ids),
            "total_profissionais": len(prof_ids),
            "total_procedimentos": len(proc_ids),
        }
