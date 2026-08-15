"""
Modelo de dados para o roadmap editável.
"""
import uuid as uuid_lib
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from database import Base


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="planejado")
    priority = Column(String(20), nullable=False, default="media")
    order = Column(Integer, nullable=False, default=0)
    done = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<RoadmapItem(title='{self.title}', status='{self.status}')>"
