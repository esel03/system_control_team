from sqlalchemy import Uuid, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from main.db.connect import Base


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид команды"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id"))
    room_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rooms.room_id"))
    role: Mapped[str] = mapped_column(String(100), comment="роль в команде")
    tag: Mapped[str] = mapped_column(
        String(100), comment="направление деятельности в команде"
    )
    is_chief: Mapped[bool] = mapped_column(
        Boolean, default=False, unique=True, comment="является ли лидером команды"
    )
