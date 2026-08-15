"""
Configuração do pytest para RAAS-CAPS.

Usa banco SQLite em arquivo temporário para isolamento.
"""
import os
import tempfile

_test_db = os.path.join(tempfile.gettempdir(), "test_raas_caps.db")
if os.path.exists(_test_db):
    os.remove(_test_db)

os.environ["DATABASE_URL"] = f"sqlite:///{_test_db}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "true"

import pytest
from fastapi.testclient import TestClient

from database import Base, get_db, engine, SessionLocal
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Cria tabelas uma vez por sessão de teste."""
    import usuario.usuario_model  # noqa: F401
    import paciente.paciente_model  # noqa: F401
    import profissional.profissional_model  # noqa: F401
    import procedimento.procedimento_model  # noqa: F401
    import registro.registro_model  # noqa: F401
    import config.config_model  # noqa: F401
    import roadmap.roadmap_model  # noqa: F401
    import sistema.log_model  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(_test_db):
        os.remove(_test_db)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Limpa dados e rate limits entre testes."""
    from sistema.rate_limit_middleware import reset_rate_limits
    reset_rate_limits()
    yield
    reset_rate_limits()
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture(scope="function")
def db_session():
    """Sessão de banco para uso direto em testes."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client():
    """Cliente de teste sem autenticação."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def auth_client(db_session):
    """Cliente autenticado como admin."""
    from usuario.usuario_service import UsuarioService

    UsuarioService.inicializar_admin_padrao(db_session)

    with TestClient(app) as c:
        c.post("/login", data={"username": "admin", "password": "admin"})
        yield c
