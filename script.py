import os
from argparse import ArgumentParser
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from tzlocal import get_localzone


def get_argumentParser():
    try:
        configParser = ConfigParser()
        configParser.read(os.path.expanduser('~/.invisibleroads'))
        timezone = configParser.get('user', 'timezone')
    except (NoSectionError, NoOptionError):
        timezone = get_localzone().zone

    argumentParser = ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+',
        help='text files with goals in hierarchical order')
    argumentParser.add_argument(
        '-t', '--timezone', metavar='TZ', default=timezone,
        help='specify target timezone')
    return argumentParser
