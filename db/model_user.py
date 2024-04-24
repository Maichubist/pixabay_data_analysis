from sqlalchemy import Column, Integer, String
from db.database import Base

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user = Column(String)
    userImageURL = Column(String)
