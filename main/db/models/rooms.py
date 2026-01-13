from db.connect import Base
from sqlalchemy import String, List, Uuid
from sqlalchemy.orm import Mapped, mapped_column
import uuid


class Rooms(Base):
    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    list_role: Mapped[List[str]] = mapped_column(List(String(70)))
    list_tag: Mapped[List[str]] = mapped_column(List(String(70)))
