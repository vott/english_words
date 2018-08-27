from sqlalchemy import Table, Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Word(Base):
    __tablename__ = 'word'
    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=False, unique=True)
    titles = relationship("Title")

class Title(Base):
    __tablename__ = 'title'
    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey('word.id'))

def register_tables(engine):
    Base.metadata.create_all(engine)
