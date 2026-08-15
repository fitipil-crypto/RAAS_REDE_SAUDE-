"""
Rotas da API para backup.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from backup.backup_service import BackupService
from sistema.auth import require_role

router = APIRouter(prefix="/api/backup", tags=["Backup"])


@router.get("/download")
def download_backup(request: Request, db: Session = Depends(get_db)):
    require_role(request, db, "admin", "operador", "coordenador")
    data = BackupService.criar_backup(db)
    content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    from datetime import datetime
    filename = f"backup_raas_caps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/restaurar")
async def restaurar_backup(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require_role(request, db, "admin")
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Arquivo inválido: {str(e)}")
    result = BackupService.restaurar_backup(db, data)
    return result
