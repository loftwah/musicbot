import time
import os
import logging
import string
import random
import functools
import click
import click_spinner
from click_didyoumean import DYMGroup
from tqdm import tqdm
from .config import config
from .lib import seconds_to_human, find_files, filecount
from .music.file import File, supported_formats

logger = logging.getLogger(__name__)

DEFAULT_MB_CONCURRENCY = 8
concurrency_options = [
    click.option('--concurrency', envvar='MB_CONCURRENCY', help='Number of coroutines', default=DEFAULT_MB_CONCURRENCY, show_default=True),
]


logger = logging.getLogger(__name__)


def random_password(size=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for i in range(size))


class GroupWithHelp(DYMGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @click.command('help')
        @click.argument('command', nargs=-1)
        @click.pass_context
        def _help(ctx, command):
            '''Print help'''
            if command:
                argument = command[0]
                c = self.get_command(ctx, argument)
                print(c.get_help(ctx))
            else:
                print(ctx.parent.get_help())
        self.add_command(_help)


def timeit(f):
    @functools.wraps(f)
    def wrapper(*args, **params):
        start = time.time()
        result = f(*args, **params)
        for_human = seconds_to_human(time.time() - start)
        if config.timings:
            logger.info('TIMINGS %s: %s', f.__name__, for_human)
        return result
    return wrapper


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


@timeit
def genfiles(folders):
    with click_spinner.spinner(disable=config.quiet):
        count = 0
        directories = [os.path.abspath(f) for f in folders]
        for d in directories:
            count += filecount(d, supported_formats)
        logger.info("File count: {}".format(count))
    with tqdm(total=count, desc="Music listing", leave=False, disable=config.quiet) as bar:
        for f in find_files(list(folders)):
            if f[1].endswith(tuple(supported_formats)):
                yield File(f[1], f[0])
            bar.update(1)