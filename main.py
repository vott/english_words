import asyncio
import aiohttp 

web = aiohttp.web
from utils import save_words, fetch_results


async def spam(request):
    """View for fetching duckduckgo results
    it could be in it's own file but it's not
    necessary.
    
    Arguments:
        request {request} -- Request object
    
    Returns:
        Json Response, Contains 3 results for a search
    """

    word = request.match_info.get('word', 'Anonymous')
    url='https://duckduckgo.com/html/'
    results  = await fetch_results(url, word)
    data = {word:results}
    return web.json_response(data)



def init():
    """Config aiohttp app
    
    Returns:
        app
    """

    app = web.Application()
    app.router.add_get('/search/duckduckgo/{word}', spam)
    return app

if(__name__ == '__main__'):
    init()