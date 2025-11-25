# SQLAlchemy models
from datetime import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm.decl_api import DeclarativeBase

Base: DeclarativeBase = declarative_base()


class PRStatus(enum.Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class Team(Base):
    __tablename__ = "teams"
    team_name = Column(String, primary_key=True, index=True)
    members = relationship("User", back_populates="team")


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    team_name = Column(String, ForeignKey("teams.team_name"))
    team = relationship("Team", back_populates="members")
    reviews = relationship("PullRequestReviewer", back_populates="reviewer")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    pull_request_id = Column(String, primary_key=True, index=True)
    pull_request_name = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"))
    status = Column(Enum(PRStatus), default=PRStatus.OPEN)
    createdAt = Column(DateTime, default=datetime.utcnow)
    mergedAt = Column(DateTime, nullable=True)
    author = relationship("User")
    reviewers = relationship("PullRequestReviewer", back_populates="pull_request")


class PullRequestReviewer(Base):
    __tablename__ = "pull_request_reviewers"
    id = Column(String, primary_key=True)
    pull_request_id = Column(String, ForeignKey("pull_requests.pull_request_id"))
    reviewer_id = Column(String, ForeignKey("users.user_id"))
    pull_request = relationship("PullRequest", back_populates="reviewers")
    reviewer = relationship("User", back_populates="reviews")
