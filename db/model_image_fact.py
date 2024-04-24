from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base

class ImageFacts(Base):
    __tablename__ = 'image_facts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    type_id = Column(Integer, ForeignKey('image_types.type_id'))
    tag1_id = Column(Integer, ForeignKey('tags.tag_id'))
    tag2_id = Column(Integer, ForeignKey('tags.tag_id'))
    tag3_id = Column(Integer, ForeignKey('tags.tag_id'))
    views = Column(Integer)
    downloads = Column(Integer)
    collections = Column(Integer)
    likes = Column(Integer)
    comments = Column(Integer)
    imageWidth = Column(Integer)
    imageHeight = Column(Integer)
    imageSize = Column(Integer)
    largeImageURL = Column(String)
    pageURL = Column(String)
    created_at = Column(DateTime, default=func.now())

    user = relationship("Users")
    image_type = relationship("ImageTypes")
    tag1 = relationship("Tags", foreign_keys=[tag1_id])
    tag2 = relationship("Tags", foreign_keys=[tag2_id])
    tag3 = relationship("Tags", foreign_keys=[tag3_id])
