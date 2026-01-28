from main.db.base import Base
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
import uuid


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид комнаты"
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="название комнаты"
    )
