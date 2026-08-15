"""
Rotas da API para importação RAAS.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from importacao.importacao_service import ImportacaoService
from sistema.auth import require_role

router = APIRouter(prefix="/api/importacao", tags=["Importação RAAS"])

MAX_ARQUIVOS = 6


def _decode(content: bytes) -> str:
    try:
        return content.decode("latin1")
    except Exception:
        return content.decode("utf-8", errors="replace")


async def _ler_arquivos(files: list[UploadFile]) -> list[tuple[str, str]]:
    if len(files) > MAX_ARQUIVOS:
        raise HTTPException(status_code=400, detail=f"Máximo de {MAX_ARQUIVOS} arquivos por vez")
    arquivos = []
    for file in files:
        content = await file.read()
        arquivos.append((file.filename, _decode(content)))
    return arquivos


@router.post("/parse")
async def parse_arquivo(request: Request, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    arquivos = await _ler_arquivos(files)
    return ImportacaoService.parse_arquivos(arquivos)


@router.post("/importar")
async def importar_arquivo(request: Request, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    arquivos = await _ler_arquivos(files)
    return ImportacaoService.do_import_arquivos(db, arquivos)
