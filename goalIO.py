import re
from whenIO import WhenIO


STATUS_PENDING, STATUS_NEXT, STATUS_DONE, STATUS_CANCELLED = xrange(4)
STATUS_CHARACTERS = '-=+_'
PATTERN_LEADSPACE = re.compile(r'(\s+)(.*)')
PATTERN_STATUS = re.compile(r'([%s])(.*)' % STATUS_CHARACTERS)
PATTERN_WHEN = re.compile(r'\[([^\]]*)\]')
PATTERN_WHITESPACE = re.compile(r'\s+')
INDENT_UNIT = '    '


class GoalFactory(object):

    def __init__(self, whenIO=None):
        self.whenIO = whenIO or WhenIO()

    def parse_line(self, text):
        # Extract
        text, leadspace = extract_leadspace(text)
        text, status = extract_status(text)
        text, start, end = extract_when(text, self.whenIO)
        # Reduce
        text = PATTERN_WHITESPACE.sub(' ', text).strip()
        level = len(leadspace)
        # Assemble
        return Goal(text, status, level, start, end, self.whenIO)

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
                 start=None, end=None, whenIO=None, inUTC=False):
        # Set parameters
        self.text = text
        self.status = status
        self.level = level
        self.start = start
        self.end = end
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

    def format(self, template='%(status)s%(text)s%(when)s', omitStartDate=False):
        leadspace = ' ' * self.level
        status = STATUS_CHARACTERS[self.status] + ' ' if self.status > STATUS_PENDING else ''
        when_ = self.whenIO.format(
            timestamps=[self.start, self.end],
            omitStartDate=omitStartDate,
            forceDate=True,
            fromUTC=self.inUTC)
        when = ' [%s]' % when_ if self.start else ''
        return template % dict(
            self.__dict__,
            leadspace=leadspace,
            status=status,
            when_=when_,
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


def extract_when(text, whenIO):
    start, end = None, None
    matches = PATTERN_WHEN.findall(text)
    if matches:
        # Remove matches from text
        text = PATTERN_WHEN.sub('', text)
        # Parse
        timestamps = whenIO.parse(' '.join(matches).lower(), toUTC=False)[0]
        if timestamps:
            start = timestamps[0]
            if len(timestamps) > 1:
                end = timestamps[-1]
    return text, start, end


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
