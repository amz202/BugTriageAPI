import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now():
    return datetime.now(timezone.utc)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    users: Mapped[List["User"]] = relationship(back_populates="team")


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True)  # e.g., 'browser_core', 'network'

    users: Mapped[List["User"]] = relationship(secondary="user_labels", back_populates="labels")


class UserLabel(Base):
    __tablename__ = "user_labels"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    label_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("labels.id"), primary_key=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("teams.id"))

    team: Mapped[Optional["Team"]] = relationship(
        back_populates="users",
        lazy="selectin"
    )
    labels: Mapped[List["Label"]] = relationship(
        secondary="user_labels",
        back_populates="users",
        lazy="selectin"
    )
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reported_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # ML Outputs
    predicted_component: Mapped[Optional[str]] = mapped_column(String(50))
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    priority: Mapped[Optional[str]] = mapped_column(String(20))
    resolution_time_days: Mapped[Optional[float]] = mapped_column(Float)
    attention_weights: Mapped[Optional[dict]] = mapped_column(JSON)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), default="pending_triage")

    assignment: Mapped[Optional["TicketAssignment"]] = relationship(back_populates="ticket", uselist=False)
    comments: Mapped[List["Comment"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"), unique=True)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    assigned_label_name: Mapped[str] = mapped_column(String(50))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    ticket: Mapped["Ticket"] = relationship(back_populates="assignment")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    ticket: Mapped["Ticket"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")