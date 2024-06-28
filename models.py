import os
from sqlalchemy import create_engine, Column, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(String, primary_key=True)
    file_path = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=False)

DATABASE_URL = 'sqlite:///resumes.db'

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()