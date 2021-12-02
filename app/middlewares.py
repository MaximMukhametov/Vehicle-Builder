from aiohttp.web import middleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker


@middleware
async def db_session_middleware(request, handler):
    """Create database session.

    We need to have an independent database session/connection per request, use the same session
    through all the request and then close it after the request is finished.
    And then a new session will be created for the next request.

    """
    async_session = sessionmaker(request.app["db"], expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        async with session.begin():
            request["db_session"] = session
            response = await handler(request)

        await session.commit()
    return response
