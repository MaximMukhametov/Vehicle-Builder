from aiohttp.web import middleware


@middleware
async def db_session(request, handler):
    resp = await handler(request)
    resp.text = resp.text + ' wink'
    return resp
