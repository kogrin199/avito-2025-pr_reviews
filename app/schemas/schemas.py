# Pydantic schemas for API
import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.models import models as db_models


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

    model_config = {"from_attributes": True}


class Team(BaseModel):
    team_name: str
    members: list[TeamMember]

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    """
    Response wrapper for Team
    """

    team: Team


class User(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """
    Response wrapper for User
    """

    user: User


class PullRequestSchema(BaseModel):
    """
    Pydantic schema for PullRequest according to OpenAPI spec
    """

    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: list[str]
    createdAt: datetime.datetime | None = None
    mergedAt: datetime.datetime | None = None

    model_config = {"from_attributes": True}


# псевдоним для обратной совместимости
PullRequest = PullRequestSchema


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str


class PullRequestResponse(BaseModel):
    """
    Response with PR
    """

    pr: PullRequestSchema


class PullRequestReassignResponse(BaseModel):
    """
    Response to reassign request with PR and new reviewer
    """

    pr: PullRequestSchema
    replaced_by: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# =======
# Converter functions: SQLAlchemy models - Pydantic schemas
# =======


def team_to_schema(team: "db_models.Team") -> Team:
    """
    Convert SQLAlchemy Team to Pydantic schema
    """
    return Team(
        team_name=team.team_name,
        members=[
            TeamMember(
                user_id=m.user_id,
                username=m.username,
                is_active=m.is_active,
            )
            for m in team.members
        ],
    )


def user_to_schema(user: "db_models.User") -> User:
    """
    Convert SQLAlchemy User to Pydantic schema
    """
    return User(
        user_id=user.user_id,
        username=user.username,
        team_name=user.team_name,
        is_active=user.is_active,
    )


def pr_to_schema(pr: "db_models.PullRequest") -> PullRequestSchema:
    """
    Convert SQLAlchemy PullRequest to Pydantic schema with assigned_reviewers
    """
    return PullRequestSchema(
        pull_request_id=pr.pull_request_id,
        pull_request_name=pr.pull_request_name,
        author_id=pr.author_id,
        status=pr.status.value if hasattr(pr.status, "value") else pr.status,
        assigned_reviewers=[r.reviewer_id for r in pr.reviewers],
        createdAt=pr.createdAt,
        mergedAt=pr.mergedAt,
    )
