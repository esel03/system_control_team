from main.db.base import Base
from typing import List
from sqlalchemy import String, Uuid, JSON
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
    list_role: Mapped[List[str]] = mapped_column(
        JSON, comment="список ролей/должностей"
    )
    list_tag: Mapped[List[str]] = mapped_column(
        JSON, comment="список направлений ответственности/сфер"
    )
