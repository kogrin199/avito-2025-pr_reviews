# Pydantic schemas for API
from datetime import datetime

from pydantic import BaseModel


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool

class Team(BaseModel):
    team_name: str
    members: list[TeamMember]

class User(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool

class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str
    assigned_reviewers: list[str]
    createdAt: datetime | None = None
    mergedAt: datetime | None = None

class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: str

class ErrorResponse(BaseModel):
    error: dict
