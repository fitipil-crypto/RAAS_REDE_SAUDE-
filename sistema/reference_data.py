"""
Tabelas de referência do sistema RAAS-CAPS.

Centraliza todos os mapas/dicionários de domínio (SIGTAP, CBO, raça,
sexo, nacionalidades etc.) para evitar duplicação entre módulos.
"""
import json
import os
import unicodedata


# ─── Mapas de domínio ────────────────────────────────────────────────
RACE_MAP = {"01": "Branca", "02": "Preta", "03": "Parda", "04": "Amarela", "05": "Indígena"}
GENDER_MAP = {"M": "Masculino", "F": "Feminino"}
SERVICE_TYPE_MAP = {"01": "Individual", "02": "Grupo", "03": "Família"}
ORIGIN_MAP = {
    "01": "Demanda Espontânea", "02": "Atenção Básica", "03": "Urgência",
    "04": "Outro CAPS", "05": "Hospital Dia", "06": "Hospital Psiquiátrico",
}

# ─── SIGTAP (procedimentos psicossociais mais usados no CAPS) ─────────
# Chaves nos dois formatos (raw 10 dígitos e formatado XX.XX.XX.XXX-X)
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

# ─── CBO (ocupações) ─────────────────────────────────────────────────
CBO_NAMES = {
    "225133": "Médico Psiquiatra",
    "225120": "Médico Clínico",
    "225125": "Médico Clínico Geral",
    "251510": "Psicólogo Clínico",
    "251515": "Psicólogo Social",
    "251545": "Psicólogo Educacional",
    "251605": "Assistente Social",
    "223505": "Enfermeiro",
    "223565": "Enfermeiro de Saúde Mental",
    "223905": "Terapeuta Ocupacional",
    "322230": "Técnico em Saúde Mental",
    "322205": "Auxiliar de Enfermagem",
    "322415": "Técnico de Enfermagem (Saúde Mental)",
    "223815": "Fonoaudiólogo",
    "223605": "Farmacêutico",
    "223710": "Nutricionista",
    "251330": "Pedagogo",
    "239425": "Arteterapeuta",
    "263105": "Musicoterapeuta",
    "224120": "Profissional de Educação Física na Saúde",
    "251310": "Educador Social",
    "251410": "Terapeuta Ocupacional",
}

# ─── Serviços / Classificações RAAS ──────────────────────────────────
SRV_OPTS = [
    {"value": "115", "label": "115 — Serviço de Atenção Psicossocial"},
    {"value": "113", "label": "113 — Serviço de Atenção Domiciliar"},
]
CLS_OPTS = [
    {"value": "002", "label": "002 — Atendimento Psicossocial"},
    {"value": "001", "label": "001 — Residência Terapêutica em Saúde Mental"},
    {"value": "004", "label": "004 — Serviço Residencial Terapêutico Tipo I"},
    {"value": "005", "label": "005 — Serviço Residencial Terapêutico Tipo II"},
    {"value": "007", "label": "007 — UA Infantojuvenil"},
]

# Equipe exibida (somente informativo) no formulário de Novo Registro RAAS.
# Edite aqui se o código/nome da equipe mudar.
DEFAULT_TEAM_CODE = "0000001123"
DEFAULT_TEAM_NAME = "Equipe Multiprofissional Atenção Especializada em Saúde Mental"

# ─── Nacionalidades ──────────────────────────────────────────────────
NACIONALIDADES = [
    {"code": "010", "name": "Brasileiro(a)"},
    {"code": "020", "name": "Naturalizado(a) Brasileiro(a)"},
    {"code": "030", "name": "Argentino(a)"},
    {"code": "040", "name": "Boliviano(a)"},
    {"code": "050", "name": "Chileno(a)"},
    {"code": "060", "name": "Paraguaio(a)"},
    {"code": "070", "name": "Uruguaio(a)"},
    {"code": "080", "name": "Venezuelano(a)"},
    {"code": "087", "name": "Haitiano(a)"},
    {"code": "175", "name": "Outros"},
]


# ─── Helpers SIGTAP ──────────────────────────────────────────────────
def only_digits(s):
    return "".join(c for c in (s or "") if c.isdigit())


def fmt_sigtap(raw):
    """0301080208 → 03.01.08.020-8"""
    d = only_digits(raw).rjust(10, "0")[:10]
    return f"{d[0:2]}.{d[2:4]}.{d[4:6]}.{d[6:9]}-{d[9]}"


def get_sigtap_name(raw_or_fmt):
    """Lookup seguro: tenta formato direto, raw e formatado."""
    if not raw_or_fmt:
        return None
    if raw_or_fmt in SIGTAP_NAMES:
        return SIGTAP_NAMES[raw_or_fmt]
    raw = only_digits(raw_or_fmt).rjust(10, "0")
    if raw in SIGTAP_NAMES:
        return SIGTAP_NAMES[raw]
    fmt = fmt_sigtap(raw) if len(raw) == 10 else raw_or_fmt
    return SIGTAP_NAMES.get(fmt)


# ─── Helpers de texto para exportação posicional ─────────────────────
def sanitize(s):
    """Remove acentos e converte para maiúsculas (padrão DATASUS)."""
    s = s or ""
    nfkd = unicodedata.normalize("NFD", s)
    no_accents = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    return no_accents.upper().strip()


# ─── Município (código IBGE → nome/UF) ────────────────────────────────
_MUNICIPIOS_PATH = os.path.join(os.path.dirname(__file__), "data_municipios_ibge.json")
_municipios_cache = None


def _municipios():
    global _municipios_cache
    if _municipios_cache is None:
        with open(_MUNICIPIOS_PATH, encoding="utf-8") as f:
            _municipios_cache = json.load(f)
    return _municipios_cache


def get_municipio(codigo):
    """Código IBGE do município (6 ou 7 dígitos, com ou sem DV) → (nome, uf).

    O leiaute RAAS permite o dígito verificador em branco, então o código
    às vezes chega com 6 dígitos só. Sempre buscamos pelos 6 primeiros.
    Retorna (None, None) se o código não for reconhecido.
    """
    digits = only_digits(codigo or "")
    if len(digits) < 6:
        return None, None
    nome_uf = _municipios().get(digits[:6])
    if not nome_uf:
        return None, None
    return nome_uf[0], nome_uf[1]


def buscar_municipios(query, uf=None, limit=20):
    """Busca municípios pelo nome (substring, sem acento/case) → lista de
    {codigo, nome, uf}, ordenada por relevância (prefixo primeiro)."""
    q = sanitize(query or "")
    if len(q) < 2:
        return []
    uf = (uf or "").strip().upper() or None

    prefixo, contem = [], []
    for codigo, (nome, muni_uf) in _municipios().items():
        if uf and muni_uf != uf:
            continue
        nome_sanit = sanitize(nome)
        if nome_sanit.startswith(q):
            prefixo.append({"codigo": codigo, "nome": nome, "uf": muni_uf})
        elif q in nome_sanit:
            contem.append({"codigo": codigo, "nome": nome, "uf": muni_uf})

    prefixo.sort(key=lambda m: m["nome"])
    contem.sort(key=lambda m: m["nome"])
    return (prefixo + contem)[:limit]
