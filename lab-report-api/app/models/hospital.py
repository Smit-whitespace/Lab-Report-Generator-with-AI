from sqlalchemy import Column, Integer, String

from app.db.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    updated_at = Column(String, nullable=False)
