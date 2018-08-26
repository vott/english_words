# async def listen_to_redis(app):
#     try:
#         sub = await aioredis.create_redis(('localhost', 6379), loop=app.loop)
#         ch, *_ = await sub.subscribe('news')
#         async for msg in ch.iter(encoding='utf-8'):
#             # Forward message to all connected websockets:
#             for ws in app['websockets']:
#                 await ws.send_str('{}: {}'.format(ch.name, msg))
#             print("message in {}: {}".format(ch.name, msg))
#     except asyncio.CancelledError:
#         pass
#     finally:
#         print('Cancel Redis listener: close connection...')
#         await sub.unsubscribe(ch.name)
#         await sub.quit()
#         print('Redis connection closed.')

# async def start_background_tasks(app):
#     app['redis_listener'] = app.loop.create_task(listen_to_redis(app))

# async def cleanup_background_tasks(app):
#     print('cleanup background tasks...')
#     app['redis_listener'].cancel()
#     await app['redis_listener']