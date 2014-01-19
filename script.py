import datetime
import dateutil.parser
import os
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from argparse import ArgumentParser
from glob import glob
from tzlocal import get_localzone


APPLICATION_NAME = 'invisibleroads'
CONFIG_FOLDER = os.path.expanduser('~/.' + APPLICATION_NAME)
CONFIG_NAME = 'default.cfg'


def get_argument_parser():
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        'source_paths', nargs='*', default=glob('*.goals'),
        help='paths to text files with goals in hierarchical order')
    argument_parser.add_argument(
        '-c', '--config_folder', metavar='FOLDER', default=CONFIG_FOLDER,
        help='configuration folder, e.g. %s' % CONFIG_FOLDER)
    argument_parser.add_argument(
        '-t', '--target_timezone', metavar='TIMEZONE',
        help='target timezone, e.g. US/Eastern')
    argument_parser.add_argument(
        '-z', '--default_time', metavar='TIME', default=datetime.time(18),
        type=lambda x: dateutil.parser.parse(x).time(),
        help='default time if unspecified, e.g. 6pm')
    return argument_parser


def get_args(argument_parser):
    args = argument_parser.parse_args()
    config_path = os.path.join(args.config_folder, CONFIG_NAME)
    config_parser = ConfigParser()
    config_parser.read(config_path)
    if not args.target_timezone:
        try:
            args.target_timezone = config_parser.get('main', 'timezone')
        except (NoSectionError, NoOptionError):
            args.target_timezone = get_localzone().zone
    try:
        args.client_id = config_parser.get('calendar', 'client_id')
        args.client_secret = config_parser.get('calendar', 'client_secret')
        args.developer_key = config_parser.get('calendar', 'developer_key')
    except (NoSectionError, NoOptionError):
        args.client_id, args.client_secret, args.developer_key = '', '', ''
    return args
