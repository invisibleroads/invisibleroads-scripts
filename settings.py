from datetime import datetime
from os.path import expanduser


DATABASE_PATH = expanduser('~/Projects/invisibleroads-missions/goals.sqlite')
DEFAULT_TIMEZONE = datetime.utcnow().astimezone().tzinfo
ID_LENGTH = 7
INDENT = '    '
