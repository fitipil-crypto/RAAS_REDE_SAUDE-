"""
RAAS-CAPS - Sistema de Gestão de Atendimentos Psicossociais
Aplicação FastAPI modular baseada na arquitetura do projeto Fluxi.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, criar_tabelas, SessionLocal
from logging_config import configurar_logging
from usuario.usuario_service import UsuarioService
from config.config_service import ConfigService
from sistema.log_middleware import LogMiddleware
from sistema.rate_limit_middleware import RateLimitMiddleware

logger = configurar_logging(debug=os.getenv("DEBUG", "false").lower() == "true")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando RAAS-CAPS...")
    criar_tabelas()
    db = SessionLocal()
    try:
        UsuarioService.inicializar_admin_padrao(db)
        ConfigService.inicializar_config_padrao(db)
        from roadmap.roadmap_service import RoadmapService
        RoadmapService.inicializar_seeds(db)
        from sistema.retention_service import RetentionService
        removed = RetentionService.purge_old_competencias(db)
        if removed:
            logger.info(f"Retenção: {removed} registro(s) antigo(s) removido(s).")
        logger.info("RAAS-CAPS iniciado com sucesso.")
    finally:
        db.close()
    yield


app = FastAPI(title="RAAS-CAPS", version="4.27", description="Sistema de Gestão de Atendimentos Psicossociais", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "raas-caps-secret-key-change-in-production"),
    session_cookie="raas_caps_session",
    max_age=86400,
)

templates = Jinja2Templates(directory="templates")

os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("exports", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LogMiddleware)


# ── Importar e registrar routers ──
from usuario.usuario_router import router as usuario_api_router
from usuario.usuario_frontend_router import router as usuario_frontend_router
from paciente.paciente_router import router as paciente_api_router
from paciente.paciente_frontend_router import router as paciente_frontend_router
from profissional.profissional_router import router as profissional_api_router
from profissional.profissional_frontend_router import router as profissional_frontend_router
from procedimento.procedimento_router import router as procedimento_api_router
from procedimento.procedimento_frontend_router import router as procedimento_frontend_router
from registro.registro_router import router as registro_api_router
from registro.registro_frontend_router import router as registro_frontend_router
from config.config_router import router as config_api_router
from config.config_frontend_router import router as config_frontend_router
from importacao.importacao_router import router as importacao_api_router
from importacao.importacao_frontend_router import router as importacao_frontend_router
from exportacao.exportacao_router import router as exportacao_api_router
from exportacao.exportacao_frontend_router import router as exportacao_frontend_router
from relatorio.relatorio_router import router as relatorio_api_router
from relatorio.relatorio_frontend_router import router as relatorio_frontend_router
from backup.backup_router import router as backup_api_router
from backup.backup_frontend_router import router as backup_frontend_router
from roadmap.roadmap_router import router as roadmap_api_router
from roadmap.roadmap_frontend_router import router as roadmap_frontend_router
from sistema.log_router import router as log_api_router
from sistema.log_frontend_router import router as log_frontend_router
from sistema.excluir_router import router as excluir_api_router
from sistema.excluir_frontend_router import router as excluir_frontend_router

# API routers
app.include_router(usuario_api_router)
app.include_router(paciente_api_router)
app.include_router(profissional_api_router)
app.include_router(procedimento_api_router)
app.include_router(registro_api_router)
app.include_router(config_api_router)
app.include_router(importacao_api_router)
app.include_router(exportacao_api_router)
app.include_router(relatorio_api_router)
app.include_router(backup_api_router)
app.include_router(roadmap_api_router)
app.include_router(log_api_router)
app.include_router(excluir_api_router)

# Frontend routers
app.include_router(usuario_frontend_router)
app.include_router(paciente_frontend_router)
app.include_router(profissional_frontend_router)
app.include_router(procedimento_frontend_router)
app.include_router(registro_frontend_router)
app.include_router(config_frontend_router)
app.include_router(importacao_frontend_router)
app.include_router(exportacao_frontend_router)
app.include_router(relatorio_frontend_router)
app.include_router(backup_frontend_router)
app.include_router(roadmap_frontend_router)
app.include_router(log_frontend_router)
app.include_router(excluir_frontend_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    """Página principal - redireciona para login ou dashboard."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user = UsuarioService.obter_por_id(db, user_id)
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    from paciente.paciente_service import PacienteService
    from profissional.profissional_service import ProfissionalService
    from procedimento.procedimento_service import ProcedimentoService
    from registro.registro_service import RegistroService
    from datetime import datetime, timedelta

    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    mes = RegistroService.estatisticas_mes(db, current_month)

    stats = {
        "total_pacientes": PacienteService.contar_todos(db),
        "total_profissionais": ProfissionalService.contar_todos(db),
        "total_procedimentos": ProcedimentoService.contar_todos(db),
        "total_registros": RegistroService.contar_todos(db),
        "unique_patients": mes["pacientes"],
        "month_records": mes["registros"],
        "active_procs": mes["procedimentos"],
        "avg": round(mes["registros"] / max(mes["pacientes"], 1), 1),
    }

    inicio_7dias = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    contagem_dias = RegistroService.contagem_por_dia(db, inicio_7dias)

    last7 = []
    max_count = 1
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        count = contagem_dias.get(d_str, 0)
        last7.append({"label": d.strftime("%d/%m"), "count": count})
        max_count = max(max_count, count)

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "stats": stats,
        "last7": last7,
        "max_count": max_count,
        "active_page": "dashboard",
    })


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {
        "error": None})


@app.post("/login")
async def login_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    user = UsuarioService.autenticar(db, username, password)
    if not user:
        from sistema.log_service import LogService
        LogService.registrar(db, action="LOGIN", username=username, method="POST", path="/login", status_code=401, details="Credenciais inválidas")
        return templates.TemplateResponse(request, "login.html", {
        "error": "Usuário ou senha inválidos"
        })

    request.session["user_id"] = user.id
    UsuarioService.atualizar_ultimo_login(db, user.id)
    from sistema.log_service import LogService
    LogService.registrar(db, action="LOGIN", user_id=user.id, username=user.username, method="POST", path="/login", status_code=200, details="Login bem-sucedido")
    return RedirectResponse(url="/", status_code=302)


@app.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    username = None
    if user_id:
        user = UsuarioService.obter_por_id(db, user_id)
        if user:
            username = user.username
    from sistema.log_service import LogService
    LogService.registrar(db, action="LOGOUT", user_id=user_id, username=username, method="GET", path="/logout", status_code=200, details="Logout")
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
