import asyncio
import aiohttp 

web = aiohttp.web
from utils import save_words, fetch_results


async def spam(request):
    word = request.match_info.get('word', 'Anonymous')
    url='https://duckduckgo.com/html/'
    results  = await fetch_results(url, word)
    print(results)
    return web.json_response(results)



def init():
    app = web.Application()
    app.router.add_get('/spam/{word}', spam)
    return app

