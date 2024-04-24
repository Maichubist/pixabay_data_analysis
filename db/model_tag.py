from sqlalchemy import Column, Integer, String
from db.database import Base

class Tags(Base):
    __tablename__ = 'tags'
    tag_id = Column(Integer, primary_key=True)
    tag = Column(String)