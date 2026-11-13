import uuid
from sqlalchemy import Column, String, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.models.base import Base


class Codebase(Base):
    __tablename__ = "codebases"

    codebase_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    owner_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False)
    project_id = Column(Uuid, ForeignKey("projects.project_id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="codebases")
    project = relationship("Project", back_populates="codebases")
    scans = relationship("Scan", back_populates="codebase", cascade="all, delete-orphan")

