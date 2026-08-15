"""
Rotas da API para o roadmap.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from roadmap.roadmap_service import RoadmapService
from roadmap.roadmap_schema import RoadmapItemResposta, RoadmapItemCriar, RoadmapItemAtualizar

router = APIRouter(prefix="/api/roadmap", tags=["Roadmap"])


def _require_auth(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user_id


@router.get("/", response_model=list[RoadmapItemResposta])
def listar(request: Request, db: Session = Depends(get_db)):
    _require_auth(request)
    return RoadmapService.listar_todos(db)


@router.get("/{item_id}", response_model=RoadmapItemResposta)
def obter(request: Request, item_id: str, db: Session = Depends(get_db)):
    _require_auth(request)
    item = RoadmapService.obter_por_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@router.post("/", response_model=RoadmapItemResposta)
def criar(request: Request, data: RoadmapItemCriar, db: Session = Depends(get_db)):
    _require_auth(request)
    return RoadmapService.criar(db, data)


@router.put("/{item_id}", response_model=RoadmapItemResposta)
def atualizar(request: Request, item_id: str, data: RoadmapItemAtualizar, db: Session = Depends(get_db)):
    _require_auth(request)
    item = RoadmapService.atualizar(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@router.patch("/{item_id}/toggle", response_model=RoadmapItemResposta)
def toggle_done(request: Request, item_id: str, db: Session = Depends(get_db)):
    _require_auth(request)
    item = RoadmapService.toggle_done(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@router.delete("/{item_id}")
def deletar(request: Request, item_id: str, db: Session = Depends(get_db)):
    _require_auth(request)
    if not RoadmapService.deletar(db, item_id):
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return {"success": True}
