from datetime import datetime
from invisibleroads_macros.disk import make_folder
from invisibleroads_macros.exceptions import InvisibleRoadsError
from os import environ
from os.path import dirname, expanduser, join


CONFIGURATION_PATH = expanduser('~/.invisibleroads/configuration.ini')
ID_LENGTH = 7
INDENT = '    '


def get_value(d, section_name, option_name, default_value=None):
    try:
        v = d[section_name][option_name]
    except KeyError:
        if default_value is None:
            raise
        v = default_value
    if option_name.endswith('folder') or option_name.endswith('path'):
        v = expanduser(v)
    return v


def get_archive_folder(d):
    v = '~/.invisibleroads'
    return get_value(d, 'archive', 'folder', v)


def get_database_url(d):
    section = d['database']
    try:
        dialect = section['dialect']
    except KeyError:
        dialect = 'sqlite'
    if dialect == 'sqlite':
        path = get_database_path(d)
        make_folder(dirname(path))
        return f'{dialect}:///{path}'
    try:
        username = get_value('database', 'username')
        password = get_value('database', 'password')
        host = get_value('database', 'host')
        port = get_value('database', 'port')
        name = get_value('database', 'name')
    except KeyError as e:
        raise InvisibleRoadsError(f'database {e} required for {dialect}')
    return f'{dialect}://{username}:{password}@{host}:{port}/{name}'


def get_database_path(d):
    v = join(get_archive_folder(d), 'goals.sqlite')
    return get_value(d, 'database', 'path', v)


def get_editor_command(d):
    v = environ.get('EDITOR', 'vim')
    return get_value(d, 'editor', 'command', v)


def get_editor_timezone(d):
    v = datetime.utcnow().astimezone().tzinfo
    return get_value(d, 'editor', 'timezone', v)


def get_folder_by_terms(d):
    folder_by_terms = {}
    section = d['archive']
    keys = [k.replace('.terms', '') for k in section if k.endswith('.terms')]
    for key in keys:
        terms = tuple(section[key + '.terms'])
        folder = section[key + '.folder']
        folder_by_terms[terms] = folder
    return folder_by_terms
