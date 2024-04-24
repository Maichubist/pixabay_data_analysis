from sqlalchemy import Column, Integer, String
from db.database import Base

class ImageTypes(Base):
    __tablename__ = 'image_types'
    type_id = Column(Integer, primary_key=True)
    type = Column(String)
