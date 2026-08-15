"""
Rotas da API para profissionais.
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from profissional.profissional_schema import ProfissionalResposta, ProfissionalCriar, ProfissionalAtualizar
from profissional.profissional_service import ProfissionalService
from sistema.auth import require_auth, require_role
from sistema.csv_import_export import build_csv, parse_csv, normalize_bool

router = APIRouter(prefix="/api/profissionais", tags=["Profissionais"])


@router.get("/", response_model=List[ProfissionalResposta])
def listar_profissionais(request: Request, search: str = Query(None), db: Session = Depends(get_db)):
    require_auth(request)
    return ProfissionalService.listar_todos(db, search)


@router.get("/ativos", response_model=List[ProfissionalResposta])
def listar_profissionais_ativos(request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    return ProfissionalService.listar_todos(db, ativos_only=True)


@router.get("/{profissional_id}", response_model=ProfissionalResposta)
def obter_profissional(profissional_id: str, request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    prof = ProfissionalService.obter_por_id(db, profissional_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return prof


@router.post("/", response_model=ProfissionalResposta)
def criar_profissional(data: ProfissionalCriar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    return ProfissionalService.criar(db, data)


@router.put("/{profissional_id}", response_model=ProfissionalResposta)
def atualizar_profissional(profissional_id: str, data: ProfissionalAtualizar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    prof = ProfissionalService.atualizar(db, profissional_id, data)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return prof


@router.delete("/{profissional_id}")
def deletar_profissional(profissional_id: str, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    success = ProfissionalService.deletar(db, profissional_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return {"mensagem": "Profissional excluído com sucesso"}


@router.post("/deletar-varios")
def deletar_varios(ids: List[str], request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    count = ProfissionalService.deletar_varios(db, ids)
    return {"mensagem": f"{count} profissional(is) excluído(s)"}


PROF_COLUMNS = ["name", "cpf", "cns", "cbo", "specialty", "team", "active"]


@router.get("/exportar/csv")
def exportar_profissionais_csv(request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    profs = ProfissionalService.listar_todos(db)
    rows = [{c: getattr(p, c) for c in PROF_COLUMNS} for p in profs]
    content = build_csv(rows, PROF_COLUMNS, ["Nome", "CPF", "CNS", "CBO", "Especialidade", "Equipe", "Ativo"])
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=profissionais.csv"}
    )


@router.post("/importar/csv")
async def importar_profissionais_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    content = await file.read()
    rows = parse_csv(content)
    stats = {"novos": 0, "atualizados": 0, "erros": 0}

    for row in rows:
        try:
            data = {c: row.get(c, None) or None for c in PROF_COLUMNS}
            data["active"] = normalize_bool(data.get("active"))

            existing = None
            if data.get("cns"):
                existing = ProfissionalService.obter_por_cns(db, data["cns"])
            if not existing and data.get("cpf"):
                existing = ProfissionalService.obter_por_cpf(db, data["cpf"])
            if not existing and data.get("name"):
                existing = ProfissionalService.obter_por_nome(db, data["name"])

            if existing:
                update_data = {k: v for k, v in data.items() if v is not None}
                ProfissionalService.atualizar(db, existing.id, ProfissionalAtualizar(**update_data))
                stats["atualizados"] += 1
            else:
                ProfissionalService.criar(db, ProfissionalCriar(**data))
                stats["novos"] += 1
        except Exception:
            stats["erros"] += 1

    return {"success": True, "mensagem": f"Importação concluída: {stats['novos']} novos, {stats['atualizados']} atualizados, {stats['erros']} erros", "stats": stats}
