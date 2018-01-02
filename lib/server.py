# -*- coding: utf-8 -*-
import time
import asyncpg
import asyncio
from datetime import datetime
from sanic_openapi import swagger_blueprint, openapi_blueprint
from logging import warning
from .lib import bytesToHuman, secondsToHuman, find_files
from . import file
from .config import config
from .collection import Collection
from .web.helpers import env, template, get_flashed_messages, download_title, server
from .web.api import api_v1
from .web.collection import collection
from .web.app import app
# from sanic import response
# from .web.limiter import limiter
# from logging_tree import printout
# printout()

app.blueprint(collection)
app.blueprint(api_v1)
app.blueprint(openapi_blueprint)
app.blueprint(swagger_blueprint)
env.globals['server_name'] = 'api.musicbot.ovh'
env.globals['get_flashed_messages'] = get_flashed_messages
env.globals['url_for'] = app.url_for
env.globals['server'] = server
env.globals['bytesToHuman'] = bytesToHuman
env.globals['secondsToHuman'] = secondsToHuman
env.globals['download_title'] = download_title
env.globals['request_time'] = lambda: secondsToHuman(time.time() - env.globals['request_start_time'])
session = {}

app.config.WTF_CSRF_SECRET_KEY = 'top secret!'
app.config.DB = Collection()
app.config.CONFIG = config
app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'Musicbot API'
app.config.API_DESCRIPTION = 'Musicbot API'
app.config.API_TERMS_OF_SERVICE = 'Use with caution!'
app.config.API_PRODUCES_CONTENT_TYPES = ['application/json']
app.config.API_CONTACT_EMAIL = 'crunchengine@gmail.com'


async def fullscan(ctx):
    folders = await ctx.obj.db.folders()
    files = [f for f in find_files(list(folders)) if f[1].endswith(tuple(filter.default_formats))]

    async def insert(semaphore, f):
        async with semaphore:
            try:
                m = file.File(f[1], f[0])
                if ctx.obj.crawl:
                    await m.find_youtube()
                await ctx.obj.db.upsert(m)
            except asyncpg.exceptions.CheckViolationError as e:
                warning("Violation: {}".format(e))
    semaphore = asyncio.BoundedSemaphore(ctx.obj.concurrency)
    tasks = [asyncio.ensure_future(insert(semaphore, f)) for f in files]
    await asyncio.gather(*tasks)


# app.add_task()


@app.middleware('request')
async def before(request):
    env.globals['request_start_time'] = time.time()
    request['session'] = session


@app.middleware('response')
async def after(request, response):
    if 'DEV' in app.config:
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'


@app.route("/")
async def get_root(request):
    return await template('index.html')

app.static('/static', './lib/web/templates/static')
