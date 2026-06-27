from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    layer_id: Mapped[str] = mapped_column(ForeignKey("layers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="demo")

    layer: Mapped["Layer"] = relationship(back_populates="products")
    radar_files: Mapped[list["RadarFile"]] = relationship(back_populates="product")
