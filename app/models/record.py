from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user = relationship("User", back_populates="records")

    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # income / expense
    category = Column(String(100), nullable=False)
    sub_category = Column(String(100), nullable=True)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    source = Column(String(20), nullable=False, default="manual")
    reference_id = Column(String(100), nullable=True)
    currency = Column(String(3), nullable=False, default="INR")

    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_records_amount_positive"),
        CheckConstraint("type IN ('income','expense')", name="ck_records_type_valid"),
        CheckConstraint("source IN ('manual','import','system')", name="ck_records_source_valid"),
        Index("ix_records_user_is_deleted_date", "user_id", "is_deleted", "date"),
        Index("ix_records_user_type_date", "user_id", "type", "date"),
    )