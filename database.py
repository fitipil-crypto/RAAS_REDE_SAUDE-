"""
Configuração do banco de dados SQLAlchemy.

Migrações automáticas: ao adicionar uma nova coluna a um modelo, basta
acrescentar uma tupla (tabela, coluna, tipo_sql) na lista _MIGRATIONS abaixo.
Na próxima inicialização a coluna é criada via ALTER TABLE se ainda não
existir — idempotente, funciona em SQLite e PostgreSQL.
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./raas_caps.db")

IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_POSTGRES = DATABASE_URL.startswith("postgres")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if IS_SQLITE else {},
    pool_pre_ping=True,
    echo=False,
)

if IS_SQLITE:
    # WAL: leituras (navegacao, relatorios) nao ficam mais bloqueadas
    # esperando escritas concorrentes (ex: log de auditoria a cada request).
    # Sem isso, o modo padrao do SQLite trava o arquivo inteiro a cada commit.
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Lista de migrações (tabela, coluna, tipo_sql) ──
# Para adicionar uma nova coluna a uma tabela existente, basta incluir
# uma nova tupla aqui. A coluna será criada automaticamente no próximo boot.
_MIGRATIONS = [
    ("pacientes", "carate", "VARCHAR(2)"),
    ("pacientes", "street_code", "VARCHAR(10)"),
    ("pacientes", "mot_saida", "VARCHAR(2)"),
]


def _run_migrations():
    """Adiciona colunas novas em tabelas existentes (idempotente)."""
    if not _MIGRATIONS:
        return
    with engine.connect() as conn:
        for table, column, col_type in _MIGRATIONS:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                ))
                conn.commit()
                print(f"[MIGRATION] Adicionada coluna {table}.{column}")
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                msg = str(e).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    pass  # Coluna já existe — esperado
                else:
                    print(f"[MIGRATION] Aviso em {table}.{column}: {e}")



# ── Índices adicionais (tabela, nome, coluna) ──
# CREATE INDEX IF NOT EXISTS já é idempotente por si só (não precisa de try/except).
_INDICES = [
    ("registros_raas", "ix_registros_raas_service_date", "service_date"),
]


def _criar_indices():
    with engine.connect() as conn:
        for table, index_name, column in _INDICES:
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
            ))
        conn.commit()


def criar_tabelas():
    """Cria todas as tabelas e roda migrações automáticas."""
    # Importar todos os modelos para registrar no Base.metadata
    import usuario.usuario_model  # noqa: F401
    import paciente.paciente_model  # noqa: F401
    import profissional.profissional_model  # noqa: F401
    import procedimento.procedimento_model  # noqa: F401
    import registro.registro_model  # noqa: F401
    import config.config_model  # noqa: F401
    import roadmap.roadmap_model  # noqa: F401
    import sistema.log_model  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_migrations()
    _criar_indices()
