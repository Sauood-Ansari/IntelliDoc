from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.membership import AccessStatus, MembershipStatus


class ProjectAccessCreate(BaseModel):
    project_id: UUID


class TeamMembershipCreate(BaseModel):
    team_id: UUID


class ApprovalDecision(BaseModel):
    decision: Literal["Approve", "Reject"]
    note: str | None = Field(None, max_length=500)


class ProjectAccessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    request_id: UUID
    project_id: UUID
    project_name: str
    team_lead_id: UUID
    requester_name: str
    requester_email: str
    status: AccessStatus
    requested_at: datetime
    decided_at: datetime | None
    decided_by: UUID | None
    decision_note: str | None


class TeamMembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    membership_id: UUID
    team_id: UUID
    team_name: str
    project_id: UUID | None
    project_name: str | None
    programmer_id: UUID
    requester_name: str
    requester_email: str
    status: MembershipStatus
    requested_at: datetime
    decided_at: datetime | None
    decided_by: UUID | None
    decision_note: str | None
