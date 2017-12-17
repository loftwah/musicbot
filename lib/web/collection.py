# -*- coding: utf-8 -*-
from logging import debug
from urllib.parse import quote, unquote
from sanic import Blueprint, response
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import PickleSerializer
from .helpers import download_title, template, basicauth, send_file
from .forms import FilterForm
from .app import app
from .filter import WebFilter
collection = Blueprint('collection', url_prefix='/collection')


@collection.get("/stats", strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def stats(request):
    '''Music library statistics'''
    db = app.config['DB']
    mf = WebFilter(request)
    stats = await db.stats(mf)
    debug(stats)
    return await template('stats.html', stats=stats)


@collection.route("/generate", strict_slashes=True)
@basicauth
async def generate(request):
    '''Generate a playlist step by step'''
    db = app.config['DB']
    # precedent = request.form
    mf = WebFilter(request)
    records = await db.form(mf)
    form = FilterForm()
    form.initialize(records)
    return await template('generate.html', form=form)


@collection.route("/consistency", strict_slashes=True)
@basicauth
async def consistency(request):
    '''Consistency'''
    return await template('consistency.html')


@collection.route("/keywords", strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def keywords(request):
    '''Get keywords'''
    db = app.config['DB']
    mf = WebFilter(request)
    keywords = await db.keywords(mf)
    return await template('keywords.html', keywords=keywords)


@collection.route("/keyword/<keyword>/artists", strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def artists_by_keyword(request, keyword):
    '''List objects related to keyword'''
    db = app.config['DB']
    mf = WebFilter(request, keywords=[keyword])
    artists = await db.artists(mf)
    return await template("keyword.html", keyword=keyword, artists=artists)


@collection.route('/genres', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def genres(request):
    '''List artists'''
    db = app.config['DB']
    mf = WebFilter(request)
    genres = await db.genres(mf)
    return await template("genres.html", genres=genres)


@collection.route('/genre/<genre>/artists', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def artists_by_genre(request, genre):
    '''List albums for artist'''
    genre = unquote(genre)
    db = app.config['DB']
    mf = WebFilter(request, genres=[genre])
    artists = await db.artists(mf)
    return await template("artists.html", artists=artists)


@collection.route('/artists', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def artists(request):
    '''List artists'''
    db = app.config['DB']
    mf = WebFilter(request)
    artists = await db.artists(mf)
    return await template("artists.html", artists=artists)


@collection.route('/artist/<artist>/albums', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def albums(request, artist):
    '''List albums for artist'''
    artist = unquote(artist)
    db = app.config['DB']
    mf = WebFilter(request, artists=[artist])
    albums = await db.albums(mf)
    return await template("artist.html", artist=artist, albums=albums, keywords=mf.keywords)


@collection.route('/artist/<artist>/album/<album>/musics', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def musics(request, artist, album):
    '''List tracks for artist/album'''
    artist = unquote(artist)
    album = unquote(album)
    db = app.config['DB']
    mf = WebFilter(request, artists=[artist], albums=[album])
    musics = await db.filter(mf)
    return await template("album.html", artist=artist, album=album, musics=musics)


async def get_music(request, artist, album, title):
    artist = unquote(artist)
    album = unquote(album)
    title = unquote(title)
    db = app.config['DB']
    mf = WebFilter(request, artists=[artist], albums=[album], titles=[title])
    musics = await db.filter(mf)
    if len(musics) != 1:
        return ('Too much music : ' + str(len(musics)), 404)
    return musics[0]


@collection.route('/artist/<artist>/album/<album>/musics/title/<title>', strict_slashes=True)
@basicauth
@cached(cache=SimpleMemoryCache, serializer=PickleSerializer())
async def music(request, artist, album, title):
    '''Get a track tags or download it'''
    music = await get_music(request, artist, album, title)
    return await template("music.html", music=music)


@collection.route('/artist/<artist>/album/<album>/musics/title/<title>/download', strict_slashes=True)
@basicauth
async def download(request, artist, album, title):
    '''Get a track and download it'''
    music = await get_music(request, artist, album, title)
    return send_file(music, music['title'])


@collection.route("/artist/<artist>/album/<album>/musics/title/<title>/listen", strict_slashes=True)
@basicauth
async def listen(request, artist, album, title):
    music = await get_music(request, artist, album, title)
    return send_file(music=music, name=download_title(music), attachment='inline')


@collection.route("/m3u", strict_slashes=True)
@basicauth
async def m3u(request):
    db = app.config['DB']
    mf = WebFilter(request)
    musics = await db.filter(mf)
    name = request.args.get('name', 'playlist')
    headers = {}
    headers['Content-Disposition'] = 'attachment; filename={}'.format(name + '.m3u')
    return await template("m3u.html", headers=headers, musics=musics)


@collection.route("/zip", strict_slashes=True)
@basicauth
async def zip(request):
    '''Generate a playlist'''
    db = app.config['DB']
    mf = WebFilter(request)
    musics = await db.filter(mf)
    if len(musics) == 0:
        return response.text('Empty playlist')

    name = request.args.get('name', 'archive')
    headers = {}
    headers['X-Archive-Files'] = 'zip'
    headers['Content-Disposition'] = 'attachment; filename={}'.format(name + '.zip')
    import os
    # see mod_zip documentation :p
    lines = [' '.join(['-',
                       str(m['size']),
                       quote("/download" + m['path'][len(m['folder']):]),
                       os.path.join(m['artist'], m['album'], os.path.basename(m['path']))])
             for m in musics]
    body = '\n'.join(lines)
    debug(body)
    return response.HTTPResponse(headers=headers, body=body)


@collection.route("/player", strict_slashes=True)
@basicauth
async def player(request):
    db = app.config['DB']
    mf = WebFilter(request)
    musics = await db.filter(mf)
    return await template('player.html', musics=musics)
