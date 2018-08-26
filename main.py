import asyncio
import os
import random
import time  

from aiohttp import web
from bs4 import BeautifulSoup
from datetime import datetime
from fake_useragent import UserAgent

from utils import save_words

async def custom_sleep():  
    print('SLEEP {}\n'.format(datetime.now()))
    await asyncio.sleep(1)
    
async def factorial(name, number):  
    f = 1
    for i in range(2, number+1):
        print('Task {}: Compute factorial({})'.format(name, i))
        await custom_sleep()
        f *= i
    print('Task {}: factorial({}) is {}\n'.format(name, number, f))


async def spam(request):
    start = time.time()  
    task1 = factorial('AA', 9)
    task2 = factorial('B', 12)
    await asyncio.gather(task1, task2)
    end = time.time()  
    return web.Response(text=f'total:{end - start}')

async def spam_sync(request):
    start = time.time()  
    await factorial('AA', 9)
    await factorial('B', 12)
    end = time.time()  
    return web.Response(text=f'total:{end - start}')



def init():
    words = save_words()
    app = web.Application()
    app.router.add_get('/spam', spam)
    app.router.add_get('/spam2', spam_sync)
    # app.on_startup.append(start_background_tasks)
    # app.on_cleanup.append(cleanup_background_tasks)
    return app

