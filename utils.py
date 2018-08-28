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
    """Setup of the database, we could use a config file for this parameters 
    as an improvement 
    
    Returns:
        sqlalchemy engine
    """

    user = 'bard'
    password = 'STORY'
    database = 'story'
    DSN = f"postgresql://{user}:{password}@postgres:5432/{database}"
    engine = create_engine(DSN)
    register_tables(engine)
    return engine

logging.getLogger().setLevel(logging.INFO)
engine = setup_database()
session = Session(engine)
Base = automap_base()
Base.prepare(engine, reflect=True)
Word = Base.classes.word
Title = Base.classes.title

def get_or_create(session, model, **kwargs):
    """Equivalent functionality to django's get_or-create for sqlalchemy
    source:
    https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create
    
    Arguments:
        session -- sqlalchemy db session
        model -- sqlalchemy db model
    
    Returns:
        sqlalchemy row
    """

    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        try:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
        except Exception as e:
            logging.warning('Exception: {}'.format(e))
            session.rollback()
        return instance

def fetch_proxies(url='https://www.sslproxies.org/', table_id='proxylisttable'):
    """Fetches a list of proxy server by parsing it form the url / table id provided
    it could be more verstile but for the use case is enough.
    
    Keyword Arguments:
        url {str} -- an url (default: {'https://www.sslproxies.org/'})
        table_id {str} -- css id of a table (default: {'proxylisttable'})
    
    Returns:
        list -- a list of dicts composed by 'ip' and 'port'
    """

    ua = UserAgent()
    proxies = []
    proxies_req = requests.get(url, headers={'User-Agent': ua.random})
    proxies_doc = proxies_req.text
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id=table_id)
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
        'ip':   row.find_all('td')[0].string,
        'port': row.find_all('td')[1].string
        })
    return proxies

def fetch_words(url='https://raw.githubusercontent.com/dwyl/english-words/master/words.txt'):
    """Fetches, preprocesses and filters (starts with lowercase letter and only allows letters after)
    an online file with words separetad by linebreaks
    
    Keyword Arguments:
        url {str} -- An url (default: {'https://raw.githubusercontent.com/dwyl/english-words/master/words.txt'})
    
    Returns:
        list -- list of words
    """

    words_req = requests.get(url)
    words_doc = words_req.text
    data = str.splitlines(words_doc)
    RE_D = re.compile(r'^[a-z][a-zA-Z]*\Z')
    return list(filter(lambda string: RE_D.search(string), data))

def save_words():
    """Save list of words to sqlalchemy
    """
    words = fetch_words()
    for w in words:
        get_or_create(session, Word, **{'text': w})

def get_random_words(number=100):
    """get random words from Word model, sqlalchemy
    
    Keyword Arguments:
        number {int} -- Number of rows to fetch (default: {100})
    
    Returns:
        list -- list of words
    """

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

async def fetch_results(url, word):
    """fetch, parse, caches and return results from a duckduckgo
    search or the database, it could be more versatile but it is 
    sufficient for the use case
    
    Arguments:
        url {str} -- an url
        word {str} -- a word
    
    Returns:
        list -- list of results
    """
    
    instance = get_or_create(session, Word, **{'text':word})
    query = session.query(Title).filter_by(parent_id=instance.id).limit(3)
    if query.first():
        db_results = [ x.text for x in query]
        return(db_results)
    else:
        async with aiohttp.ClientSession() as ClientSession:
            try:
                response = await ClientSession.post(
                    url,
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
            cleaned_results = []
            for row in results[0:3]:
                try:
                    title_instance = Title(text=row.a.text, parent_id=instance.id)
                    session.add(title_instance)
                    session.commit()
                except:
                    session.rollback()
                cleaned_results.append(row.a.text)

        return(cleaned_results)

async def fetch_results_semaphore(proxy, url, word, client_session, semaphore):
    """Same as fetch_results but designed for concurrency and uses a semaphore
    
    Arguments:
        proxy {str} -- proxy url
        url {str} -- probably duckduckgo's url
        word {str} -- search string
        client_session {object} -- aiohttp client session
        semaphore {object} -- asyncio semaphore
    """

    ua = UserAgent()
    instance = get_or_create(session, Word, **{'text':word})
    await semaphore.acquire()
    logging.debug(f'Proxy: {proxy} URL:{url} Word: {word}')
    try:
        response = await client_session.post(
            url,
            headers={'User-Agent': ua.random},
            proxy=proxy,
            data={
                'q': word
            },
            ssl=False,
            timeout=10
        )
        html = await response.read()
        await asyncio.sleep(2)
    except Exception as e:
        logging.warning('Exception: {}'.format(e))
        return None
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.findAll("h2", {"class": "result__title"})
    titles = []
    for row in results[0:3]:
        titles.append(row.a.text)
        try:
            title_instance = Title(text=row.a.text, parent_id=instance.id)
            session.add(title_instance)
            session.commit()
        except:
            session.rollback()
    semaphore.release()
    logging.info(str(titles))

