from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid, ForeignKey, UniqueConstraint, Boolean
import uuid
from main.db.base import Base


class UsersToRooms(Base):
    __tablename__ = "users_to_rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id"))
    room_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rooms.room_id"))
    is_chief: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="является ли лидером команды"
    )

    __table_args__ = (UniqueConstraint("user_id", "room_id", name="uix_user_room"),)
