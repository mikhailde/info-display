from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.sql.schema import UniqueConstraint

from database import Base

class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('message', name='uq_content_message'),
    )
