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
    team_id = Column(Uuid, ForeignKey("teams.team_id", name="fk_codebases_team_id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="codebases")
    project = relationship("Project", back_populates="codebases")
    team = relationship("Team", back_populates="codebases")
    scans = relationship("Scan", back_populates="codebase", cascade="all, delete-orphan")

    @property
    def project_name(self):
        return self.project.project_name if self.project else None

    @property
    def team_name(self):
        return self.team.team_name if self.team else None

