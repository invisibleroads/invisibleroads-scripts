import re
from whenIO import WhenIO


STATUS_PENDING, STATUS_NEXT, STATUS_DONE, STATUS_CANCELLED = xrange(4)
STATUS_CHARACTERS = '-=+_'
PATTERN_LEADSPACE = re.compile(r'(\s+)(.*)')
PATTERN_STATUS = re.compile(r'([%s])(.*)' % STATUS_CHARACTERS)
PATTERN_WHEN = re.compile(r'\[([^\]]*)\]')
INDENT_UNIT = '  '


class GoalFactory(object):

    def __init__(self, whenIO):
        self.whenIO = whenIO

    def parse_line(self, line):
        text = line
        # Extract
        text = extract_leadspace(text)[0]
        text, status = extract_status(text)
        text, start, end = extract_when(text, self.whenIO)
        # Reduce
        text = text.strip()
        # Assemble
        return Goal(text, status, start, end, self.whenIO)


class Goal(object):

    def __init__(self, text, status=STATUS_PENDING, start=None, end=None, whenIO=None, inUTC=False):
        self.text = text
        self.status = status
        self.start = start
        self.end = end
        self.whenIO = whenIO or WhenIO()
        self.inUTC = inUTC

    def format(self, template='%(statusSymbol)s %(text)s [%(whens)s]', withStartDate=True):
        valueByKey = dict(self.__dict__,
                          statusSymbol=STATUS_CHARACTERS[self.status],
                          whens=self.whenIO.format([self.start, self.end], withStartDate=withStartDate, fromUTC=self.inUTC))
        return template % valueByKey


def extract_leadspace(text):
    'Extract leadspace from text'
    match = PATTERN_LEADSPACE.match(text)
    try:
        leadspace, text = match.groups()
    except AttributeError:
        return text, ''
    # Replace tabs with spaces
    leadspace = leadspace.replace('\t', INDENT_UNIT)
    return text, leadspace


def extract_status(text):
    match = PATTERN_STATUS.match(text)
    try:
        symbol, text = match.groups()
    except AttributeError:
        return text, 0
    else:
        return text, STATUS_CHARACTERS.index(symbol)


def extract_when(text, whenIO):
    start, end = None, None
    matches = PATTERN_WHEN.findall(text)
    if matches:
        # Remove matches from text
        text = PATTERN_WHEN.sub('', text)
        # Parse
        whens = whenIO.parse(' '.join(matches).lower(), toUTC=False)[0]
        if whens:
            start = whens[0]
            if len(whens) > 1:
                end = whens[-1]
    return text, start, end
