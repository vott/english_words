import os
import random
import re

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from sqlalchemy import (
    create_engine, MetaData
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql.expression import func, select
from fake_useragent import UserAgent
from sqlalchemy.orm import Session 

from db import register_tables, word, title

def random_proxy(proxies):
    return random.randint(0, len(proxies) - 1)
    

def setup_database():
    user = 'bard'
    password = 'STORY'
    database = 'story'
    DSN = f"postgresql://{user}:{password}@postgres:5432/{database}"
    engine = create_engine(DSN)
    meta = MetaData()
    meta.create_all(bind=engine, tables=register_tables)
    return engine

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

def fetch_proxies(url='https://www.sslproxies.org/', table_id='proxylisttable'):
    ua = UserAgent()
    proxies = []
    proxies_req = Request(url)
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id=table_id)
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
        'ip':   row.find_all('td')[0].string,
        'port': row.find_all('td')[1].string
        })
    return proxies

def fetch_words(url='https://raw.githubusercontent.com/dwyl/english-words/master/words.txt'):
    words_req = Request(url)
    words_doc = urlopen(words_req).read().decode('utf8')
    data = str.splitlines(words_doc)
    RE_D = re.compile(r'^[a-z]\D+\Z')
    data = filter(lambda string: RE_D.search(string), data)
    return data

engine = setup_database()
session = Session(engine)
Base = automap_base()
Base.prepare(engine, reflect=True)
Word = Base.classes.word
Title = Base.classes.title

def save_words():
    words = fetch_words()
    for w in words:
        get_or_create(session, word, **{'text': w})

def get_random_words(number=1):
    query = session.query(word).order_by(func.random()).limit(number)
    return ([u._asdict() for u in query])

