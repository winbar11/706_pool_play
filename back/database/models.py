from datetime import datetime

from sqlalchemy import (
    Column, ForeignKey, Integer, Table, Text, Float, TIMESTAMP, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


team_golfers = Table(
    "team_golfers",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("golfer_id", Integer, ForeignKey("golfers.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_admin: Mapped[int | None] = mapped_column(Integer, default=0)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    teams: Mapped[list["Team"]] = relationship(back_populates="user")


class Golfer(Base):
    __tablename__ = "golfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    espn_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    salary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    world_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_round: Mapped[int | None] = mapped_column(Integer, default=0)
    round1_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    round2_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    round3_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    round4_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    made_cut: Mapped[int | None] = mapped_column(Integer, default=1)
    finish_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    solo_leader_r1: Mapped[int | None] = mapped_column(Integer, default=0)
    solo_leader_r2: Mapped[int | None] = mapped_column(Integer, default=0)
    solo_leader_r3: Mapped[int | None] = mapped_column(Integer, default=0)
    solo_leader_r4: Mapped[int | None] = mapped_column(Integer, default=0)

    teams: Mapped[list["Team"]] = relationship(secondary=team_golfers, back_populates="golfers")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_name: Mapped[str] = mapped_column(Text, nullable=False)
    total_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    final_score: Mapped[int | None] = mapped_column(Integer, default=0)
    bonus_shots: Mapped[int | None] = mapped_column(Integer, default=0)
    is_locked: Mapped[int | None] = mapped_column(Integer, default=0)
    dk_total_points: Mapped[float | None] = mapped_column(Float, default=0)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    user: Mapped["User"] = relationship(back_populates="teams")
    golfers: Mapped[list["Golfer"]] = relationship(secondary=team_golfers, back_populates="teams")


class TournamentSetting(Base):
    __tablename__ = "tournament_settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    used: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
