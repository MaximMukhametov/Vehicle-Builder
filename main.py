from aiohttp import web

from db.engine import pg_context
from middlewares import db_session_middleware
from settings import config
from views import routes


async def init_app():
    app = web.Application(middlewares=[db_session_middleware])
    app.add_routes(routes)

    app['config'] = config

    # create db connection on startup, shutdown on exit
    app.cleanup_ctx.append(pg_context)

    return app


def main():
    app = init_app()
    web.run_app(app, host=config['host'], port=config['port'])


if __name__ == '__main__':
    main()
