"""
Rotas da API para procedimentos.
"""
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from procedimento.procedimento_schema import ProcedimentoResposta, ProcedimentoCriar, ProcedimentoAtualizar
from procedimento.procedimento_service import ProcedimentoService
from sistema.auth import require_auth, require_role
from sistema.csv_import_export import parse_csv, normalize_bool

router = APIRouter(prefix="/api/procedimentos", tags=["Procedimentos"])


@router.get("/", response_model=List[ProcedimentoResposta])
def listar_procedimentos(request: Request, search: str = Query(None), db: Session = Depends(get_db)):
    require_auth(request)
    return ProcedimentoService.listar_todos(db, search)


@router.get("/ativos", response_model=List[ProcedimentoResposta])
def listar_procedimentos_ativos(request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    return ProcedimentoService.listar_todos(db, ativos_only=True)


@router.get("/{procedimento_id}", response_model=ProcedimentoResposta)
def obter_procedimento(procedimento_id: str, request: Request, db: Session = Depends(get_db)):
    require_auth(request)
    proc = ProcedimentoService.obter_por_id(db, procedimento_id)
    if not proc:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    return proc


@router.post("/", response_model=ProcedimentoResposta)
def criar_procedimento(data: ProcedimentoCriar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    return ProcedimentoService.criar(db, data)


@router.put("/{procedimento_id}", response_model=ProcedimentoResposta)
def atualizar_procedimento(procedimento_id: str, data: ProcedimentoAtualizar, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "coordenador")
    proc = ProcedimentoService.atualizar(db, procedimento_id, data)
    if not proc:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    return proc


@router.delete("/{procedimento_id}")
def deletar_procedimento(procedimento_id: str, request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    success = ProcedimentoService.deletar(db, procedimento_id)
    if not success:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    return {"mensagem": "Procedimento excluído com sucesso"}


@router.post("/deletar-varios")
def deletar_varios(ids: List[str], request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    count = ProcedimentoService.deletar_varios(db, ids)
    return {"mensagem": f"{count} procedimento(s) excluído(s)"}


@router.get("/exportar/csv")
def exportar_procedimentos_csv(request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    procs = ProcedimentoService.listar_todos(db)

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Código', 'Nome', 'Descrição', 'Categoria', 'Ativo', 'Criado em'])

    for p in procs:
        writer.writerow([
            p.code,
            p.name,
            p.description or '',
            p.category or '',
            'Sim' if p.active else 'Não',
            p.created_at.strftime('%d/%m/%Y %H:%M') if p.created_at else '',
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=procedimentos.csv"}
    )


PROC_COLUMNS = ["code", "name", "description", "category", "active"]


@router.post("/importar/csv")
async def importar_procedimentos_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    content = await file.read()
    rows = parse_csv(content)
    stats = {"novos": 0, "atualizados": 0, "erros": 0}

    for row in rows:
        try:
            data = {c: row.get(c, None) or None for c in PROC_COLUMNS}
            data["active"] = normalize_bool(data.get("active"))
            if not data.get("category"):
                data["category"] = "RAAS (Atenção Psicossocial)"

            existing = ProcedimentoService.obter_por_code(db, data["code"]) if data.get("code") else None
            if existing:
                update_data = {k: v for k, v in data.items() if v is not None}
                ProcedimentoService.atualizar(db, existing.id, ProcedimentoAtualizar(**update_data))
                stats["atualizados"] += 1
            else:
                ProcedimentoService.criar(db, ProcedimentoCriar(**data))
                stats["novos"] += 1
        except Exception:
            stats["erros"] += 1

    return {"success": True, "mensagem": f"Importação concluída: {stats['novos']} novos, {stats['atualizados']} atualizados, {stats['erros']} erros", "stats": stats}
