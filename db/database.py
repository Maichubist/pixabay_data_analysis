from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def init_db(uri):
    engine = create_engine(uri)
    Base.metadata.create_all(engine)
    return engine

engine = init_db("sqlite:///db/database_warehouse.db")
SessionLocal = sessionmaker(bind=engine)
