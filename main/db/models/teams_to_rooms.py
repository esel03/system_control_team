import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from main.db.base import Base


class TeamToRoom(Base):
    __tablename__ = "teams_to_rooms"

    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид"
    )
    room_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rooms.room_id"))
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="название команды"
    )
