"""
Serviço para logs do sistema (auditoria).
"""
import uuid as uuid_lib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from sistema.log_model import LogSistema


class LogService:

    @staticmethod
    def registrar(
        db: Session,
        action: str,
        user_id: str = None,
        username: str = None,
        resource_type: str = None,
        resource_id: str = None,
        method: str = None,
        path: str = None,
        status_code: int = None,
        details: str = None,
    ) -> LogSistema:
        log = LogSistema(
            id=str(uuid_lib.uuid4()),
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            method=method,
            path=path,
            status_code=status_code,
            details=details,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def listar_todos(
        db: Session,
        action: str = None,
        user_id: str = None,
        resource_type: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[LogSistema]:
        query = db.query(LogSistema)
        if action:
            query = query.filter(LogSistema.action == action)
        if user_id:
            query = query.filter(LogSistema.user_id == user_id)
        if resource_type:
            query = query.filter(LogSistema.resource_type == resource_type)
        if date_from:
            try:
                dt_from = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(LogSistema.timestamp >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(LogSistema.timestamp < dt_to)
            except ValueError:
                pass
        return query.order_by(desc(LogSistema.timestamp)).limit(limit).offset(offset).all()

    @staticmethod
    def contar(db: Session, action: str = None, resource_type: str = None) -> int:
        query = db.query(LogSistema)
        if action:
            query = query.filter(LogSistema.action == action)
        if resource_type:
            query = query.filter(LogSistema.resource_type == resource_type)
        return query.count()

    @staticmethod
    def limpar_antigos(db: Session, dias: int = 90) -> int:
        cutoff = datetime.now() - timedelta(days=dias)
        count = db.query(LogSistema).filter(LogSistema.timestamp < cutoff).count()
        db.query(LogSistema).filter(LogSistema.timestamp < cutoff).delete()
        db.commit()
        return count
