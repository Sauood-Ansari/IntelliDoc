import uuid
from sqlalchemy import Column, Float, ForeignKey, Uuid, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class Score(Base):
    __tablename__ = "scores"

    score_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    scan_id = Column(Uuid, ForeignKey("scans.scan_id"), unique=True, nullable=False)
    programmer_id = Column(Uuid, ForeignKey("users.user_id"), nullable=False)
    documentation_score = Column(Float, nullable=True)  # Normalized 0.0 to 100.0 (SRS App C)
    code_quality_score = Column(Float, nullable=True)  # Equal to documentation_score in v1
    breakdown = Column(JSON, nullable=False)  # Breakdown: completeness, consistency, penalties

    # Relationships
    scan = relationship("Scan", back_populates="score")
    programmer = relationship("User", back_populates="scores")

