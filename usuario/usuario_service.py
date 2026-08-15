"""
Serviço para gerenciamento de usuários e autenticação.
"""
import uuid as uuid_lib
from datetime import datetime
from sqlalchemy.orm import Session
import bcrypt as _bcrypt

from usuario.usuario_model import Usuario
from usuario.usuario_schema import UsuarioCriar, UsuarioAtualizar, SenhaAtualizar


class UsuarioService:

    @staticmethod
    def inicializar_admin_padrao(db: Session):
        """Cria usuário admin padrão se não existir nenhum usuário."""
        existing = db.query(Usuario).first()
        if existing:
            return
        admin = Usuario(
            id=str(uuid_lib.uuid4()),
            username="admin",
            name="Administrador",
            role="admin",
            password_hash=_bcrypt.hashpw("admin".encode(), _bcrypt.gensalt()).decode(),
            active=True,
        )
        db.add(admin)
        db.commit()

    @staticmethod
    def autenticar(db: Session, username: str, password: str) -> Usuario | None:
        user = db.query(Usuario).filter(
            Usuario.username == username,
            Usuario.active == True
        ).first()
        if not user:
            return None
        if not _bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return None
        return user

    @staticmethod
    def obter_por_id(db: Session, user_id: str) -> Usuario | None:
        return db.query(Usuario).filter(Usuario.id == user_id).first()

    @staticmethod
    def obter_por_username(db: Session, username: str) -> Usuario | None:
        return db.query(Usuario).filter(Usuario.username == username).first()

    @staticmethod
    def listar_todos(db: Session) -> list[Usuario]:
        return db.query(Usuario).order_by(Usuario.created_at.desc()).all()

    @staticmethod
    def criar(db: Session, data: UsuarioCriar) -> Usuario:
        existing = UsuarioService.obter_por_username(db, data.username)
        if existing:
            raise ValueError("Login já existe")
        user = Usuario(
            id=str(uuid_lib.uuid4()),
            username=data.username,
            name=data.name,
            role=data.role,
            password_hash=_bcrypt.hashpw(data.password.encode(), _bcrypt.gensalt()).decode(),
            active=data.active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def atualizar(db: Session, user_id: str, data: UsuarioAtualizar) -> Usuario | None:
        user = UsuarioService.obter_por_id(db, user_id)
        if not user:
            return None
        if data.name is not None:
            user.name = data.name
        if data.role is not None:
            user.role = data.role
        if data.active is not None:
            user.active = data.active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def alterar_senha(db: Session, user_id: str, data: SenhaAtualizar) -> bool:
        user = UsuarioService.obter_por_id(db, user_id)
        if not user:
            return False
        if data.current_password:
            if not _bcrypt.checkpw(data.current_password.encode(), user.password_hash.encode()):
                raise ValueError("Senha atual incorreta")
        if data.new_password != data.confirm_password:
            raise ValueError("As senhas não coincidem")
        user.password_hash = _bcrypt.hashpw(data.new_password.encode(), _bcrypt.gensalt()).decode()
        db.commit()
        return True

    @staticmethod
    def deletar(db: Session, user_id: str) -> bool:
        user = UsuarioService.obter_por_id(db, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def atualizar_ultimo_login(db: Session, user_id: str):
        user = UsuarioService.obter_por_id(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
