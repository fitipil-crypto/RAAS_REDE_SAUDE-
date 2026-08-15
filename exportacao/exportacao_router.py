"""
Rotas da API para exportação RAAS.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from database import get_db
from exportacao.exportacao_service import ExportacaoService
from config.config_service import ConfigService
from sistema.auth import require_auth, require_role

router = APIRouter(prefix="/api/exportacao", tags=["Exportação RAAS"])


@router.get("/stats")
def stats(request: Request, month: str = Query(...), db: Session = Depends(get_db)):
    require_auth(request)
    return ExportacaoService.get_stats(db, month)


@router.get("/raas", response_class=PlainTextResponse)
def exportar_raas(
    request: Request,
    month: str = Query(...),
    suffix: str = Query("CAPSI1"),
    uf_code: str = Query(None),
    cnes_code: str = Query(None),
    organ_name: str = Query(None),
    organ_code: str = Query(None),
    cnpj: str = Query(None),
    destination_organ: str = Query(None),
    destination_indicator: str = Query(None),
    versao: str = Query(None),
    bdversao: str = Query(None),
    salvar_padrao: bool = Query(False),
    db: Session = Depends(get_db),
):
    user = require_role(request, db, "admin")
    header_overrides = {
        "uf_code": uf_code,
        "cnes_code": cnes_code,
        "organ_name": organ_name,
        "organ_code": organ_code,
        "cnpj": cnpj,
        "destination_organ": destination_organ,
        "destination_indicator": destination_indicator,
        "versao": versao,
        "bdversao": bdversao,
    }
    # Persistência: se solicitado, grava os campos do cabeçalho como padrão (somente admin)
    if salvar_padrao and user.role == "admin":
        valores = {k: v for k, v in header_overrides.items() if v is not None}
        if valores:
            ConfigService.atualizar_varios(db, valores)
    content, filename, _ = ExportacaoService.exportar_raas(
        db, month, suffix, header_overrides=header_overrides
    )
    if not content:
        raise HTTPException(status_code=404, detail="Nenhum registro encontrado para o mês")
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/cabecalho/salvar")
def salvar_cabecalho(
    request: Request,
    dados: dict,
    db: Session = Depends(get_db),
):
    """Persiste os campos do cabeçalho (Registro 01) como padrão do estabelecimento."""
    require_role(request, db, "admin")
    campos_validos = {
        "uf_code", "cnes_code", "organ_name", "organ_code", "cnpj",
        "destination_organ", "destination_indicator", "versao", "bdversao",
    }
    valores = {k: str(v) for k, v in (dados or {}).items()
               if k in campos_validos and v is not None}
    if not valores:
        raise HTTPException(status_code=400, detail="Nenhum campo válido informado")
    resultado = ConfigService.atualizar_varios(db, valores)
    return {"status": "ok", "salvos": resultado}


@router.get("/csv", response_class=PlainTextResponse)
def exportar_csv(request: Request, month: str = Query(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    content, filename, _ = ExportacaoService.exportar_csv(db, month)
    if not content:
        raise HTTPException(status_code=404, detail="Nenhum registro encontrado para o mês")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
