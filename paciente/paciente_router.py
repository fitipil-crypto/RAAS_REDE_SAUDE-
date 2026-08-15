"""
Rotas da API para pacientes.
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from config.config_service import ConfigService
from paciente.paciente_schema import PacienteResposta, PacienteCriar, PacienteAtualizar
from paciente.paciente_service import PacienteService
from sistema.auth import require_auth, require_role
from sistema.csv_import_export import build_csv, parse_csv, normalize_bool

router = APIRouter(prefix="/api/pacientes", tags=["Pacientes"])


@router.get("/", response_model=List[PacienteResposta])
def listar_pacientes(request: Request, search: str = Query(None), db: Session = Depends(get_db)):
    require_auth(request)
    return PacienteService.listar_todos(db, search)


@router.get("/municipios/buscar")
def buscar_municipios(request: Request, q: str = Query(..., min_length=2), uf: str = Query(None)):
    require_auth(request)
    from sistema.reference_data import buscar_municipios as buscar
    return buscar(q, uf)


@router.get("/municipios/codigo/{codigo}")
def resolver_municipio(codigo: str, request: Request):
    """Resolve um código IBGE (ex: vindo de importação RAAS) → nome/UF.

    Usado para preencher Cidade/UF na edição de pacientes importados, que
    têm municipality_code mas nunca tiveram city/state digitados."""
    require_auth(request)
    from sistema.reference_data import get_municipio
    nome, uf = get_municipio(codigo)
    if not nome:
        raise HTTPException(status_code=404, detail="Município não encontrado")
    return {"codigo": codigo, "nome": nome, "uf": uf}


@router.post("/cidade-padrao")
def salvar_cidade_padrao(dados: dict, request: Request, db: Session = Depends(get_db)):
    """Salva cidade/UF/código IBGE como padrão para o cadastro de novos pacientes."""
    require_role(request, db, "admin", "operador", "coordenador")
    ConfigService.atualizar_varios(db, {
        "default_city": dados.get("city") or "",
        "default_state": dados.get("state") or "",
        "default_municipality_code": dados.get("municipality_code") or "",
    })
    return {"status": "ok"}


@router.get("/{paciente_id}", response_model=PacienteResposta)
def obter_paciente(paciente_id: str, request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    paciente = PacienteService.obter_por_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return paciente


@router.post("/", response_model=PacienteResposta)
def criar_paciente(data: PacienteCriar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador", "coordenador")
    return PacienteService.criar(db, data)


@router.put("/{paciente_id}", response_model=PacienteResposta)
def atualizar_paciente(paciente_id: str, data: PacienteAtualizar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador", "coordenador")
    paciente = PacienteService.atualizar(db, paciente_id, data)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return paciente


@router.delete("/{paciente_id}")
def deletar_paciente(paciente_id: str, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    success = PacienteService.deletar(db, paciente_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return {"mensagem": "Paciente excluído com sucesso"}


@router.post("/deletar-varios")
def deletar_varios(ids: List[str], request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    count = PacienteService.deletar_varios(db, ids)
    return {"mensagem": f"{count} paciente(s) excluído(s)"}


PACIENTE_COLUMNS = [
    "name", "prontuario", "cns", "cpf", "birth_date", "gender", "race",
    "mother_name", "phone", "cell_phone", "email", "cep", "address",
    "street_number", "address_complement", "neighborhood", "city", "state",
    "municipality_code", "cid_main", "admission_date", "drug_user",
    "street_situation", "esf_coverage", "user_origin", "user_destination",
]


@router.get("/exportar/csv")
def exportar_pacientes_csv(request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    pacientes = PacienteService.listar_todos(db)
    rows = [{c: getattr(p, c) for c in PACIENTE_COLUMNS} for p in pacientes]
    headers = ["Nome", "Prontuario", "CNS", "CPF", "Nascimento", "Sexo", "Raca",
               "Nome da Mae", "Telefone", "Celular", "Email", "CEP", "Endereco",
               "Numero", "Complemento", "Bairro", "Cidade", "UF", "CodMunicipio",
               "CID Principal", "Data Admissao", "Usuario Drogas", "Situacao Rua",
               "Cobertura ESF", "Origem", "Destino"]
    content = build_csv(rows, PACIENTE_COLUMNS, headers)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=pacientes.csv"}
    )


@router.post("/importar/csv")
async def importar_pacientes_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    content = await file.read()
    rows = parse_csv(content)
    stats = {"novos": 0, "atualizados": 0, "erros": 0}

    for row in rows:
        try:
            data = {c: row.get(c, None) or None for c in PACIENTE_COLUMNS}
            data["drug_user"] = "S" if str(data.get("drug_user") or "").strip().lower() in ("sim", "s", "yes", "true", "1") else "N"
            data["street_situation"] = "S" if str(data.get("street_situation") or "").strip().lower() in ("sim", "s", "yes", "true", "1") else "N"
            data["esf_coverage"] = "S" if str(data.get("esf_coverage") or "").strip().lower() in ("sim", "s", "yes", "true", "1") else "N"

            existing = None
            if data.get("cns"):
                existing = PacienteService.obter_por_cns(db, data["cns"])
            if not existing and data.get("cpf"):
                existing = PacienteService.obter_por_cpf(db, data["cpf"])

            if existing:
                update_data = {k: v for k, v in data.items() if v is not None}
                PacienteService.atualizar(db, existing.id, PacienteAtualizar(**update_data))
                stats["atualizados"] += 1
            else:
                PacienteService.criar(db, PacienteCriar(**data))
                stats["novos"] += 1
        except Exception:
            stats["erros"] += 1

    return {"success": True, "mensagem": f"Importação concluída: {stats['novos']} novos, {stats['atualizados']} atualizados, {stats['erros']} erros", "stats": stats}
