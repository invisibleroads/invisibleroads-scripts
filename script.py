import os
from argparse import ArgumentParser
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from tzlocal import get_localzone


APPLICATION_NAME = 'invisibleroads'
CONFIG_FOLDER = os.path.expanduser('~/.' + APPLICATION_NAME)
CONFIG_NAME = 'default.cfg'


def get_argumentParser():
    argumentParser = ArgumentParser()
    argumentParser.add_argument(
        'sourcePath', nargs='+',
        help='text file with goals in hierarchical order')
    argumentParser.add_argument(
        '-c', '--config', metavar='FOLDER',
        dest='configFolder', default=CONFIG_FOLDER,
        help='configuration folder, e.g. %s' % CONFIG_FOLDER)
    argumentParser.add_argument(
        '-t', '--timezone', metavar='TIMEZONE',
        help='target timezone, e.g. US/Eastern')
    return argumentParser


def get_args(argumentParser):
    args = argumentParser.parse_args()
    args.sourcePaths = args.sourcePath
    configPath = os.path.join(args.configFolder, CONFIG_NAME)
    configParser = ConfigParser()
    configParser.read(configPath)
    if not args.timezone:
        try:
            args.timezone = configParser.get('main', 'timezone')
        except (NoSectionError, NoOptionError):
            args.timezone = get_localzone().zone
    try:
        args.clientId = configParser.get('calendar', 'clientId')
        args.clientSecret = configParser.get('calendar', 'clientSecret')
        args.developerKey = configParser.get('calendar', 'developerKey')
    except (NoSectionError, NoOptionError):
        args.clientId, args.clientSecret, args.developerKey = '', '', ''
    return args
