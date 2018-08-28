import aiohttp
import asyncio
import logging
import random

from fake_useragent import UserAgent

from utils import fetch_proxies, fetch_words, fetch_results_semaphore


async def main():
    """ Fetch and cache random words,
    it works poorly because the proxies provided aren't good
    """

    semaphore = asyncio.BoundedSemaphore(value=8)
    async with aiohttp.ClientSession() as session:
        limit=5
        url='https://duckduckgo.com/html/'
        ua = UserAgent()
        proxies = fetch_proxies()
        proxies_size = len(proxies)
        # 100 random words
        words = random.sample(fetch_words(), 100)
        tasks = []
        for index in range(1, proxies_size):
            proxy = proxies[index]
            ip = proxy['ip']
            port = proxy['port']
            proxy_url = f'http://{ip}:{port}'
            lower = ((index-1)*limit)
            higher = index*limit
            for word in words[lower:higher]:
                tasks.append(fetch_results_semaphore(proxy_url, url, word, session, semaphore))
        await asyncio.wait(tasks)

if(__name__ == '__main__'):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    logging.info('Finito')