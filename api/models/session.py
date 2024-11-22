import datetime
from database import Base
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True,autoincrement=True) 
    session_id= Column(String(36), primary_key=True, index=True) 
    created_on = Column(DateTime, default=func.now())

    history = relationship("History", back_populates="session", cascade="all, delete")






