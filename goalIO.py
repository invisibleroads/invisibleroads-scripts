import re
from dateutil.relativedelta import relativedelta
from whenIO import WhenIO, parse_duration, format_duration


STATUS_PENDING, STATUS_NEXT, STATUS_DONE, STATUS_CANCELLED = xrange(4)
STATUS_CHARACTERS = '-=+_'
PATTERN_LEADSPACE = re.compile(r'(\s+)(.*)')
PATTERN_STATUS = re.compile(r'([%s])(.*)' % STATUS_CHARACTERS)
PATTERN_WHEN = re.compile(r'\[([^\]]*)\]')
PATTERN_WHITESPACE = re.compile(r'\s+')
INDENT_UNIT = '    '
GOAL_TEMPLATE = '%(status)s%(text)s%(when)s'


class GoalFactory(object):

    def __init__(self, whenIO=None, inUTC=True):
        self.whenIO = whenIO or WhenIO()
        self.inUTC = inUTC

    def parse_line(self, text):
        # Extract
        text, leadspace = extract_leadspace(text)
        text, status = extract_status(text)
        text, start, duration = extract_when(text, self.whenIO, self.inUTC)
        # Reduce
        text = PATTERN_WHITESPACE.sub(' ', text).strip()
        level = len(leadspace)
        # Assemble
        return Goal(
            text,
            status,
            level,
            start,
            duration,
            self.whenIO,
            self.inUTC)

    def parse_hierarchy(self, lines):
        lineage = [Goal()]
        previous = None
        for line in lines:
            if not line.strip():
                continue
            goal = self.parse_line(line)
            level = goal.level
            if previous:
                if level > previous.level:
                    lineage.append(previous)
                elif level < previous.level:
                    while len(lineage) > 1 and level <= lineage[-1].level:
                        lineage.pop()
            goal.parent = lineage[-1]
            previous = goal
        return lineage[0].children


class Goal(object):

    def __init__(self, text='', status=STATUS_PENDING, level=0,
                 start=None, duration=None, whenIO=None, inUTC=True):
        # Set parameters
        self.text = text
        self.status = status
        self.level = level
        self.start = start
        self.duration = duration
        self.whenIO = whenIO or WhenIO()
        self.inUTC = inUTC
        # Set variables
        self._parent = None
        self.children = []

    def __str__(self):
        return self.format()

    def __repr__(self):
        if self.text:
            return '<Goal: %s>' % self.text
        else:
            return '<Goal>'

    def format(self, template=GOAL_TEMPLATE, omitStartDate=False, whenIO=None):
        leadspace = ' ' * self.level
        if self.status > STATUS_PENDING:
            status = STATUS_CHARACTERS[self.status] + ' '
        else:
            status = ''
        time = (whenIO or self.whenIO).format(
            self.start,
            omitStartDate=omitStartDate,
            fromUTC=self.inUTC)
        duration = format_duration(
            self.duration, 
            style='letters', 
            rounding='ceiling')
        whenString = (time + ' ' + duration).strip()
        when = ' [%s]' % whenString if whenString else ''
        return template % dict(
            self.__dict__,
            leadspace=leadspace,
            status=status,
            time=time,
            duration=duration,
            when=when)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        parent.children.append(self)
        if parent.text:
            self._parent = parent


class GoalError(Exception):
    pass


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


def extract_when(text, whenIO, toUTC=True):
    start = None
    duration = None
    matches = PATTERN_WHEN.findall(text)
    if matches:
        # Remove matches from text
        text = PATTERN_WHEN.sub('', text)
        # Parse
        whenString = ' '.join(matches).lower()
        timestamps, terms = whenIO.parse(whenString, toUTC=toUTC)
        duration = parse_duration(' '.join(terms))
        if timestamps:
            start = timestamps[0]
            if len(timestamps) > 1:
                end = timestamps[-1]
                seconds = (end - start).total_seconds()
                if seconds:
                    duration = relativedelta(seconds=seconds)
    return text, start, duration


def load_whenIO(sourceFile):
    line = sourceFile.next()
    if line.startswith('#'):
        line = line.lstrip('# ')
        timezone = line.split()[0]
        today = WhenIO(timezone).parse(line, toUTC=False)[0][0]
        whenIO = WhenIO(timezone, today)
    else:
        whenIO = WhenIO()
        sourceFile.seek(0)
    return whenIO
