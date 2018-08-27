import aiohttp
import asyncio
import logging
import os
import random
import re
import requests

from bs4 import BeautifulSoup
from sqlalchemy import (
    create_engine, MetaData
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.sql import insert
from sqlalchemy.sql.expression import func, select
from fake_useragent import UserAgent
from sqlalchemy.orm import Session 

from db import register_tables, Word, Title

def setup_database():
    user = 'bard'
    password = 'STORY'
    database = 'story'
    DSN = f"postgresql://{user}:{password}@postgres:5432/{database}"
    engine = create_engine(DSN)
    register_tables(engine)
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
    proxies_req = requests.get(url, headers={'User-Agent': ua.random})
    proxies_doc = proxies_req.text
    soup = BeautifulSoup(proxies_doc.text, 'html.parser')
    proxies_table = soup.find(id=table_id)
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
        'ip':   row.find_all('td')[0].string,
        'port': row.find_all('td')[1].string
        })
    return proxies

def fetch_words(url='https://raw.githubusercontent.com/dwyl/english-words/master/words.txt'):
    words_req = requests.get(url)
    words_doc = words_req.text
    data = str.splitlines(words_doc)
    RE_D = re.compile(r'^[a-z]\D+\Z')
    return list(filter(lambda string: RE_D.search(string), data))

engine = setup_database()
session = Session(engine)
Base = automap_base()
Base.prepare(engine, reflect=True)
Word = Base.classes.word
Title = Base.classes.title

def save_words():
    words = fetch_words()
    for w in words:
        get_or_create(session, Word, **{'text': w})

def get_random_words(number=100):
    query = session.query(Word).order_by(
        func.random()
    ).outerjoin(Title).having(
        func.count_(Title.id) <= 1
    ).group_by(Word).limit(number)
    list_objects = []
    for r in query:
        d = {}
        for column in r.__table__.columns:
            d[column.name] = str(getattr(r, column.name))
        list_objects.append(d)
    return list_objects

async def fetch_results(proxy, agent, url, session, word):
    instance = session.query(Word).filter_by(**{'text':word}).first()
    try:
        response = await session.post(
            url,
            headers={'User-Agent': agent},
            proxie=proxy,
            data={
                'q': word
            }
        )
        html = await response.read()
    except Exception as e:
        logging.warning('Exception: {}'.format(e))
        return None
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.findAll("h2", {"class": "result__title"})
    for row in results[0:3]:
        instance.titles.append(Title(text=row))
    session.save()


async def populate_titles(limit, url='https://duckduckgo.com/html/'):
    ua = UserAgent()
    proxies = fetch_proxies()
    proxies_size = len(proxies)
    words = get_random_words()
    tasks = []
    for index in range(1, proxies_size):
        proxy = proxies[index]
        ip = proxy['ip']
        port = proxy['port']
        proxy_url = f'http://{ip}:{port}'
        async with aiohttp.ClientSession() as session:
            lower = ((index-1)*limit)
            higher = index*limit
            for word in words[lower:higher]:
                tasks.append(fetch_results(proxy_url, ua.random, url, session, word['text']))
            asyncio.wait(tasks)

