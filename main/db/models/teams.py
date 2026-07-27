import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from main.db.base import Base


class TeamMember(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид"
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teams_to_rooms.team_id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id"))
    role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="неопределена",
        server_default="неопределена",
        comment="роль в команде",
    )
    tag: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="неопределена",
        server_default="неопределена",
        comment="направление деятельности в команде",
    )
    is_chief: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="является ли руководителем команды",
    )

    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uix_team_user"),)


# Временный совместимый alias для внешних импортов.
Team = TeamMember
