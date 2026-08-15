"""
Serviço para importação de arquivos RAAS.

Lê arquivos posicionais RAAS-SIA (registros 01, 15 e 16), faz o parse,
cruza pacientes × procedimentos e cadastra automaticamente pacientes,
profissionais, procedimentos e registros.

As posições dos campos seguem o layout RAAS-SIA Abr/2025.
Para ajustar o layout, edite parse_r15 / parse_r16.
"""
import re
from collections import Counter
from sqlalchemy.orm import Session

from paciente.paciente_service import PacienteService
from paciente.paciente_schema import PacienteCriar, PacienteAtualizar
from profissional.profissional_service import ProfissionalService
from profissional.profissional_schema import ProfissionalCriar
from procedimento.procedimento_service import ProcedimentoService
from procedimento.procedimento_schema import ProcedimentoCriar
from registro.registro_service import RegistroService
from registro.registro_schema import RegistroCriar
from sistema.reference_data import CBO_NAMES, get_sigtap_name, fmt_sigtap, only_digits


def _p(line, ini, fim):
    return line[ini - 1:fim]


def _pt(line, ini, fim):
    return line[ini - 1:fim].strip()


def _nz(s):
    if not s or s.strip() == "" or re.match(r"^0+$", s.strip()):
        return ""
    return s.strip()


def _digits_nz(s):
    digits = only_digits(_nz(s))
    return "" if not digits or re.match(r"^0+$", digits) else digits


def _to_date(d):
    s = (d or "").strip()
    if not s or len(s) < 8 or re.match(r"^0+$", s):
        return ""
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"


class ImportacaoService:

    @staticmethod
    def parse_file(text: str) -> dict:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        lines = [l for l in lines if l.strip()]

        warnings = []
        header = None
        records15 = []
        records16 = []

        for li, raw_line in enumerate(lines):
            line = raw_line.ljust(420, " ")
            code = _pt(line, 1, 2)

            if code == "01":
                header = {
                    "comp": _pt(line, 8, 13),
                    "organ_name": _pt(line, 24, 53),
                    "organ_code": _pt(line, 54, 59),
                    "cnpj": _pt(line, 60, 73),
                    "dst": _pt(line, 74, 113),
                    "dst_in": _pt(line, 114, 114),
                    "dtger": _pt(line, 115, 122),
                    "versao": _pt(line, 123, 127),
                }
                continue

            if code == "15":
                cns = _nz(_p(line, 18, 32))
                cpf = _nz(_p(line, 392, 402))
                nome = _pt(line, 49, 78)
                if not nome and not cns:
                    warnings.append(f"Linha {li+1}: Reg.15 sem nome/CNS — ignorado")
                    continue

                row = {
                    "_line": li + 1,
                    "coduf": _pt(line, 3, 4),
                    "cmp": _pt(line, 5, 10),
                    "codcnes": _pt(line, 11, 17),
                    "cns": cns,
                    "cpf": cpf,
                    "nome": nome,
                    "npront": _digits_nz(_p(line, 79, 88)),
                    "nomemae": _pt(line, 89, 118),
                    "logr": _pt(line, 119, 148),
                    "numpcnte": _nz(_p(line, 149, 153)),
                    "compl": _nz(_p(line, 154, 163)),
                    "cep": _nz(_p(line, 164, 171)),
                    "mun": _nz(_p(line, 172, 178)),
                    "nasc": _pt(line, 179, 186),
                    "sexo": _pt(line, 187, 187),
                    "raca": _pt(line, 188, 189),
                    "nomeresp": _pt(line, 190, 219),
                    "nascpcnte": _pt(line, 220, 222),
                    "etnia": _nz(_p(line, 223, 226)),
                    "tel": _digits_nz(_p(line, 227, 237)),
                    "cel": _digits_nz(_p(line, 238, 248)),
                    "motsaida": _pt(line, 249, 250),
                    "dtalta": _pt(line, 251, 258),
                    "cidp": _nz(_p(line, 259, 262)),
                    "cids1": _nz(_p(line, 263, 266)),
                    "cids2": _nz(_p(line, 267, 270)),
                    "cidca": _nz(_p(line, 275, 278)),
                    "carate": _nz(_p(line, 279, 280)),
                    "origempcn": _pt(line, 281, 282),
                    "esf": _pt(line, 283, 283),
                    "cnes_esf": _nz(_p(line, 284, 290)),
                    "total_acoes": _pt(line, 291, 295),
                    "dest": _pt(line, 296, 297),
                    "sit_rua": _pt(line, 301, 301),
                    "usu_droga": _pt(line, 302, 302),
                    "tipo_droga": _pt(line, 303, 305),
                    "autorizacao": _nz(_p(line, 306, 318)),
                    "bairro": _pt(line, 319, 348),
                    "cod_logr": _nz(_p(line, 349, 351)),
                    "email": _nz(_p(line, 352, 391)),
                    "dtiinval": _pt(line, 33, 40),
                    "dtfimval": _pt(line, 41, 48),
                }
                records15.append(row)
                continue

            if code == "16":
                acao = _pt(line, 41, 50)
                if not acao or acao.replace("0", "") == "":
                    warnings.append(f"Linha {li+1}: Reg.16 sem código SIGTAP — ignorado")
                    continue
                row = {
                    "_line": li + 1,
                    "coduf": _pt(line, 3, 4),
                    "cmp": _pt(line, 5, 10),
                    "codcnes": _pt(line, 11, 17),
                    "cns_pac": _nz(_p(line, 18, 32)),
                    "acao": acao,
                    "cbo": _nz(_p(line, 51, 56)),
                    "cns_prof": _nz(_p(line, 57, 71)),
                    "dtexec": _pt(line, 72, 79),
                    "srv": _pt(line, 80, 82),
                    "cls": _pt(line, 83, 85),
                    "qtd": _pt(line, 86, 91),
                    "local": _pt(line, 95, 95),
                    "cpf_pac": _nz(_p(line, 96, 106)),
                }
                records16.append(row)
                continue

        # Listas de pré-visualização (deduplicadas) para o front-end
        pacientes = []
        seen_pac = set()
        for r in records15:
            key = r["cns"] or ("cpf:" + r["cpf"] if r["cpf"] else "nome:" + r["nome"])
            if key in seen_pac:
                continue
            seen_pac.add(key)
            pacientes.append({
                "nome": r["nome"],
                "cns": r["cns"],
                "nasc": r["nasc"],
                "sexo": r["sexo"],
                "cidp": r["cidp"],
                "cmp": r["cmp"],
            })

        procedimentos = []
        proc_idx = {}
        for r in records16:
            raw = only_digits(r["acao"] or "").rjust(10, "0")
            if not raw or raw.replace("0", "") == "":
                continue
            fmt = fmt_sigtap(raw)
            if raw in proc_idx:
                procedimentos[proc_idx[raw]]["ocorrencias"] += 1
                continue
            proc_idx[raw] = len(procedimentos)
            procedimentos.append({
                "codigo": fmt,
                "nome": get_sigtap_name(raw) or get_sigtap_name(fmt) or "",
                "ocorrencias": 1,
            })

        profissionais = []
        prof_idx = {}
        for r in records16:
            if not r["cns_prof"]:
                continue
            if r["cns_prof"] in prof_idx:
                profissionais[prof_idx[r["cns_prof"]]]["atendimentos"] += 1
                continue
            prof_idx[r["cns_prof"]] = len(profissionais)
            profissionais.append({
                "cns": r["cns_prof"],
                "cbo": r["cbo"],
                "cargo": CBO_NAMES.get(r["cbo"], ""),
                "atendimentos": 1,
            })

        resumo = {
            "total_pacientes": len(pacientes),
            "total_procedimentos": len(procedimentos),
            "total_profissionais": len(profissionais),
            "total_registros": len(records16),
        }

        return {
            "header": header,
            "records15": records15,
            "records16": records16,
            "warnings": warnings,
            "pacientes": pacientes,
            "procedimentos": procedimentos,
            "profissionais": profissionais,
            "resumo": resumo,
        }

    @staticmethod
    def do_import(db: Session, parsed: dict) -> dict:
        records15 = parsed["records15"]
        records16 = parsed["records16"]
        log = []

        cnt_pat_new = 0
        cnt_pat_upd = 0
        cnt_prof_new = 0
        cnt_proc_new = 0
        cnt_rec_new = 0
        cnt_rec_skip = 0

        # Passo 1: Pacientes
        from paciente.paciente_model import Paciente
        row15_by_id = {}
        for idx, r in enumerate(records15):
            existing = None
            if r["cns"]:
                existing = PacienteService.obter_por_cns(db, r["cns"])
            if not existing and r["cpf"]:
                existing = db.query(Paciente).filter(Paciente.cpf == r["cpf"]).first()
            if not existing and not r["cns"] and not r["cpf"]:
                existing = db.query(Paciente).filter(Paciente.name == r["nome"]).first()

            # Data de admissão não existe no leiaute RAAS — usamos a data
            # inicial de validade como origem. Em paciente já existente só
            # entra se o campo estiver vazio, para não sobrescrever edição
            # manual. Cidade/UF não são gravadas: a tela exibe sempre a
            # partir do código IBGE do município (ver reference_data.get_municipio).
            admissao_raas = _to_date(r["dtiinval"])
            extra_fields = {}
            if not existing:
                extra_fields = {"admission_date": admissao_raas}
            elif not existing.admission_date and admissao_raas:
                extra_fields["admission_date"] = admissao_raas

            pat_data = PacienteCriar(
                **extra_fields,
                name=r["nome"] or "Sem nome",
                cns=r["cns"] or "",
                cpf=r["cpf"] or "",
                prontuario=r["npront"] or "",
                birth_date=_to_date(r["nasc"]),
                gender=r["sexo"] or "",
                race=r["raca"] or "",
                nationality=r.get("nascpcnte") or "010",
                ethnicity=r.get("etnia") or "",
                carate=r.get("carate") or "",
                street_code=r.get("cod_logr") or "",
                neighborhood=r.get("bairro") or "",
                mot_saida=r.get("motsaida") or "",
                municipality_code=r["mun"] or "",
                cid_main=r["cidp"] or "",
                cid_associated1=r["cids1"] or "",
                cid_associated2=r["cids2"] or "",
                cid_causes=r["cidca"] or "",
                mother_name=r["nomemae"] or "",
                guardian_name=r["nomeresp"] or "",
                cep=r["cep"] or "",
                address=r["logr"] or "",
                street_number=r["numpcnte"] or "",
                address_complement=r["compl"] or "",
                phone=r["tel"] or "",
                cell_phone=r["cel"] or "",
                email=r["email"] or "",
                date_ini_valid=_to_date(r["dtiinval"]),
                date_fim_valid=_to_date(r["dtfimval"]),
                user_origin=r["origempcn"] or "01",
                user_destination=r["dest"] or "00",
                conclusion_date=_to_date(r["dtalta"]),
                esf_coverage=r["esf"] or "N",
                cnes_usf=r["cnes_esf"] or "",
                street_situation=r["sit_rua"] or "N",
                drug_user=r["usu_droga"] or "N",
                alcohol_user="A" in (r["tipo_droga"] or ""),
                crack_user="C" in (r["tipo_droga"] or ""),
                other_drugs_user="O" in (r["tipo_droga"] or ""),
                authorization_number=r["autorizacao"] or "",
            )

            if existing:
                update_data = PacienteAtualizar(**pat_data.model_dump(exclude_unset=True))
                PacienteService.atualizar(db, existing.id, update_data)
                pid = existing.id
                cnt_pat_upd += 1
                log.append(f"✏️ PAC atualizado: {r['nome']} (CNS:{r['cns'] or r['cpf'] or 's/doc'})")
            else:
                pac = PacienteService.criar(db, pat_data)
                pid = pac.id
                cnt_pat_new += 1
                log.append(f"✅ PAC criado: {r['nome']} (CNS:{r['cns'] or r['cpf'] or 's/doc'})")

            if r["cns"]:
                row15_by_id[r["cns"]] = pid
            if r["cpf"]:
                row15_by_id["cpf:" + r["cpf"]] = pid
            row15_by_id["idx:" + str(idx)] = pid

        # Passo 2: Profissionais
        prof_by_cns = {}
        for p in ProfissionalService.listar_todos(db):
            if p.cns:
                prof_by_cns[p.cns] = p.id

        for r in records16:
            if not r["cns_prof"]:
                continue
            if r["cns_prof"] in prof_by_cns:
                if r["cbo"]:
                    prof = ProfissionalService.obter_por_id(db, prof_by_cns[r["cns_prof"]])
                    if prof and not prof.cbo:
                        from profissional.profissional_schema import ProfissionalAtualizar
                        ProfissionalService.atualizar(db, prof.id, ProfissionalAtualizar(cbo=r["cbo"]))
                continue

            prof_data = ProfissionalCriar(
                name="Nome do profissional",
                cns=r["cns_prof"],
                cbo=r["cbo"] or "",
                specialty=CBO_NAMES.get(r["cbo"], ""),
                active=True,
            )
            prof = ProfissionalService.criar(db, prof_data)
            prof_by_cns[r["cns_prof"]] = prof.id
            cnt_prof_new += 1
            log.append(f"✅ PROF criado: Nome do profissional (CNS:{r['cns_prof']} CBO:{r['cbo']})")

        # Passo 3: Procedimentos
        proc_by_code = {}
        for p in ProcedimentoService.listar_todos(db):
            raw = re.sub(r"\D", "", p.code).zfill(10)
            proc_by_code[raw] = p.id

        for r in records16:
            raw = only_digits(r["acao"] or "").rjust(10, "0")
            if not raw or raw.replace("0", "") == "":
                continue
            if raw in proc_by_code:
                continue
            fmt = fmt_sigtap(raw)
            proc_data = ProcedimentoCriar(
                code=fmt,
                name="Nome do procedimento",
                category="RAAS (Atenção Psicossocial)",
                active=True,
            )
            proc = ProcedimentoService.criar(db, proc_data)
            proc_by_code[raw] = proc.id
            cnt_proc_new += 1
            log.append(f"✅ PROC criado: {fmt} — Nome do procedimento")

        # Passo 4: Registros RAAS
        # Contagem por chave (não um set): o próprio RAAS legitimamente repete a
        # mesma ação (paciente+procedimento+data+profissional) mais de uma vez
        # no mesmo dia. Só descartamos uma linha do arquivo se já existir, em
        # importações anteriores, uma quantidade igual ou maior de registros
        # com essa mesma chave — evitando reimportar o mesmo arquivo duas vezes
        # sem perder repetições legítimas dentro do próprio arquivo.
        existing_regs = RegistroService.listar_todos(db)
        dup_key = Counter()
        for r in existing_regs:
            dup_key[f"{r.patient_id}|{r.procedure_id}|{r.service_date}|{r.professional_id}"] += 1

        for r in records16:
            pat_id = None
            if r["cns_pac"]:
                pat_id = row15_by_id.get(r["cns_pac"])
            if not pat_id and r["cpf_pac"]:
                pat_id = row15_by_id.get("cpf:" + r["cpf_pac"])

            if not pat_id:
                cnt_rec_skip += 1
                log.append(f"⚠️ REC ignorado (sem paciente para CNS {r['cns_pac']}): linha {r['_line']}")
                continue

            raw = only_digits(r["acao"] or "").rjust(10, "0")
            proc_id = proc_by_code.get(raw)
            if not proc_id:
                cnt_rec_skip += 1
                log.append(f"⚠️ REC ignorado (proc não resolvido {r['acao']}): linha {r['_line']}")
                continue

            prof_id = prof_by_cns.get(r["cns_prof"], "")
            cmp = r["cmp"] or ""
            svc_month = f"{cmp[:4]}-{cmp[4:6]}" if len(cmp) == 6 else ""
            svc_date = _to_date(r["dtexec"]) if r["dtexec"] else (svc_month + "-01" if svc_month else "")

            dk = f"{pat_id}|{proc_id}|{svc_date}|{prof_id}"
            if dup_key[dk] > 0:
                dup_key[dk] -= 1
                cnt_rec_skip += 1
                continue

            reg_data = RegistroCriar(
                service_month=svc_month,
                service_date=svc_date,
                patient_id=pat_id,
                procedure_id=proc_id,
                professional_id=prof_id,
                cbo_code=r["cbo"] or "",
                service_type="01",
                srv=r["srv"] or "115",
                cls=r["cls"] or "002",
                local_realizacao="T" if r["local"] == "T" else "C",
                quantity=max(1, int(r["qtd"]) if r["qtd"].isdigit() else 1),
            )
            RegistroService.criar(db, reg_data)
            cnt_rec_new += 1

        # Retenção: descarta competências fora da janela permitida
        from sistema.retention_service import RetentionService
        removed = RetentionService.purge_old_competencias(db)
        if removed:
            log.append(f"🗂️ {removed} registro(s) de competências antigas descartado(s) (retenção)")

        return {
            "log": log,
            "stats": {
                "pacientes_novos": cnt_pat_new,
                "pacientes_atualizados": cnt_pat_upd,
                "profissionais_novos": cnt_prof_new,
                "procedimentos_novos": cnt_proc_new,
                "registros_novos": cnt_rec_new,
                "registros_ignorados": cnt_rec_skip,
            },
        }

    RESUMO_KEYS = ("total_pacientes", "total_procedimentos", "total_profissionais", "total_registros")
    STATS_KEYS = (
        "pacientes_novos", "pacientes_atualizados", "profissionais_novos",
        "procedimentos_novos", "registros_novos", "registros_ignorados",
    )

    @staticmethod
    def parse_arquivos(arquivos: list[tuple[str, str]]) -> dict:
        """Faz parse de vários arquivos RAAS (nome, texto) e agrega o resumo total."""
        resultados = []
        resumo_geral = {chave: 0 for chave in ImportacaoService.RESUMO_KEYS}
        for nome, texto in arquivos:
            parsed = ImportacaoService.parse_file(texto)
            resultados.append({"nome": nome, **parsed})
            for chave in ImportacaoService.RESUMO_KEYS:
                resumo_geral[chave] += parsed["resumo"].get(chave, 0)
        return {"arquivos": resultados, "resumo_geral": resumo_geral}

    @staticmethod
    def do_import_arquivos(db: Session, arquivos: list[tuple[str, str]]) -> dict:
        """Importa vários arquivos RAAS (nome, texto) em sequência e agrega stats/log."""
        resultados = []
        stats_geral = {chave: 0 for chave in ImportacaoService.STATS_KEYS}
        for nome, texto in arquivos:
            parsed = ImportacaoService.parse_file(texto)
            resultado = ImportacaoService.do_import(db, parsed)
            resultados.append({"nome": nome, **resultado})
            for chave in ImportacaoService.STATS_KEYS:
                stats_geral[chave] += resultado["stats"].get(chave, 0)
        return {"arquivos": resultados, "stats_geral": stats_geral}
