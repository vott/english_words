from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, MetaData
)

meta = MetaData()

word = Table(
    'word', meta,
    Column('id', Integer, primary_key=True),
    Column('text', String(200), nullable=False, unique=True),
)

title = Table(
    'title', meta,
    Column('id', Integer, primary_key=True),
    Column('text', String(200), nullable=False),
    Column('title_id',
           Integer,
           ForeignKey('title.id', ondelete='CASCADE'))
)

register_tables = [ word, title]