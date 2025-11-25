# SQLAlchemy models
# - using Declarative Base
# (see https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#declarative-mapping-using-declarativebase)
import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PRStatus(enum.StrEnum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class Team(Base):
    __tablename__   = "teams"
    team_name       = mapped_column(String, primary_key=True, index=True)
    members         = relationship("User", back_populates="team")


class User(Base):
    __tablename__   = "users"
    user_id         = mapped_column(String, primary_key=True, index=True)
    username        = mapped_column(String, nullable=False)
    is_active       = mapped_column(Boolean, default=True)
    team_name       = mapped_column(String, ForeignKey("teams.team_name"))
    team            = relationship("Team", back_populates="members")
    reviews         = relationship("PullRequestReviewer", back_populates="reviewer")


class PullRequest(Base):
    __tablename__   = "pull_requests"
    pull_request_id     = mapped_column(String, primary_key=True, index=True)
    pull_request_name   = mapped_column(String, nullable=False)
    author_id           = mapped_column(String, ForeignKey("users.user_id"))
    status              = mapped_column(Enum(PRStatus), default=PRStatus.OPEN)
    createdAt           = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    mergedAt            = mapped_column(DateTime(timezone=True), nullable=True)
    author              = relationship("User")
    reviewers           = relationship("PullRequestReviewer", back_populates="pull_request")


class PullRequestReviewer(Base):
    __tablename__   = "pull_request_reviewers"
    id              = mapped_column(String, primary_key=True)
    pull_request_id = mapped_column(String, ForeignKey("pull_requests.pull_request_id"))
    reviewer_id     = mapped_column(String, ForeignKey("users.user_id"))
    pull_request    = relationship("PullRequest", back_populates="reviewers")
    reviewer        = relationship("User", back_populates="reviews")
