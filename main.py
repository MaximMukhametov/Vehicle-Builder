import sys

from aiohttp import web

from db import pg_context
from settings import get_config, config


async def init_app():

    app = web.Application()

    app['config'] = config

    # create db connection on startup, shutdown on exit
    app.cleanup_ctx.append(pg_context)

    return app


def main():
    app = init_app()
    web.run_app(app, host=config['host'], port=config['port'])


if __name__ == '__main__':
    main()
