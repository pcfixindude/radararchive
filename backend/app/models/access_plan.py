from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class AccessPlan(Base):
    __tablename__ = "access_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    history_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
