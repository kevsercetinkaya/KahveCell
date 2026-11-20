from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_shops_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_shops_longitude"),
        Index("ix_shops_location", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    opening_hours: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)

    products: Mapped[list[Product]] = relationship(back_populates="shop")
    orders: Mapped[list[Order]] = relationship(back_populates="shop")