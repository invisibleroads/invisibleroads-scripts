import re
from dateutil.relativedelta import relativedelta
from whenIO import WhenIO, parse_duration, format_duration


STATUS_PENDING, STATUS_NEXT, STATUS_DONE, STATUS_CANCELLED = xrange(4)
STATUS_CHARACTERS = '-=+_'
PATTERN_LEADSPACE = re.compile(r'(\s+)(.*)')
PATTERN_STATUS = re.compile(r'([%s])(.*)' % STATUS_CHARACTERS)
PATTERN_IMPACT = re.compile(r'(.*)\[(.*)\+(\d+)(.*)\](.*)')
PATTERN_WHEN = re.compile(r'\[([^\]]*)\]')
PATTERN_WHITESPACE = re.compile(r'\s+')
INDENT_UNIT = '    '
GOAL_TEMPLATE = '%(status)s%(text)s%(properties)s'


class GoalFactory(object):

    def __init__(self, whenIO=None, in_utc=True):
        self.whenIO = whenIO or WhenIO()
        self.in_utc = in_utc

    def parse_line(self, text):
        # Extract
        text, leadspace = extract_leadspace(text)
        text, status = extract_status(text)
        text, impact = extract_impact(text)
        text, start, duration = extract_when(text, self.whenIO, self.in_utc)
        # Reduce
        text = PATTERN_WHITESPACE.sub(' ', text).strip()
        level = len(leadspace)
        # Assemble
        return Goal(
            text, level, status, impact, start, duration,
            self.whenIO, self.in_utc)

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

    def __init__(
            self, text='', level=0, status=STATUS_PENDING, impact=0,
            start=None, duration=None, whenIO=None, in_utc=True):
        # Set parameters
        self.text = text
        self.level = level
        self.status = status
        self.impact = impact
        self.start = start
        self.duration = duration
        self.whenIO = whenIO or WhenIO()
        self.in_utc = in_utc
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

    def format(
            self,
            template=GOAL_TEMPLATE,
            omit_start_date=False,
            whenIO=None):
        leadspace_string = format_leadspace(self.level)
        status_string = format_status(self.status)
        impact_string = format_impact(self.impact)
        time_string = format_time(
            whenIO or self.whenIO, self.start, omit_start_date, self.in_utc)
        duration_string = format_duration(
            self.duration, style='letters', rounding='ceiling')
        properties_string = format_properties_string([
            impact_string,
            time_string,
            duration_string])
        return template % dict(
            self.__dict__,
            leadspace=leadspace_string,
            status=status_string,
            impact=impact_string,
            time=time_string,
            duration=duration_string,
            properties=properties_string)

    @property
    def relative_impact(self):
        return self.impact

    @property
    def absolute_impact(self):
        absolute_impact = self.impact
        parent = self.parent
        while parent:
            absolute_impact += parent.impact
            parent = parent.parent
        return absolute_impact

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


def extract_impact(text):
    try:
        text1, text2, impact, text3, text4 = PATTERN_IMPACT.match(
            text).groups()
    except AttributeError:
        return text, 0
    return '%s [%s %s] %s' % (text1, text2, text3, text4), int(impact)


def extract_when(text, whenIO, to_utc=True):
    start = None
    duration = None
    matches = PATTERN_WHEN.findall(text)
    if matches:
        # Remove matches from text
        text = PATTERN_WHEN.sub('', text)
        # Parse
        when_string = ' '.join(matches).lower()
        timestamps, terms = whenIO.parse(when_string, toUTC=to_utc)
        duration = parse_duration(' '.join(terms))
        if timestamps:
            start = timestamps[0]
            if len(timestamps) > 1:
                end = timestamps[-1]
                seconds = (end - start).total_seconds()
                if seconds:
                    duration = relativedelta(seconds=seconds)
    return text, start, duration


def format_leadspace(level):
    return ' ' * level


def format_status(status):
    if status <= STATUS_PENDING:
        return ''
    return STATUS_CHARACTERS[status] + ' '


def format_time(whenIO, start, omit_start_date, from_utc):
    return whenIO.format(
        start, omitStartDate=omit_start_date, fromUTC=from_utc)


def format_impact(impact):
    if not impact:
        return ''
    return '%+d' % impact


def format_properties_string(properties):
    string = ' '.join(_.strip() for _ in properties if _.strip()).strip()
    return ' [%s]' % string if string else ''


def yield_goal(source_path, default_time):
    with open(source_path) as source_file:
        goal_factory = GoalFactory(get_whenIO(source_file, default_time))
        for line in source_file:
            yield goal_factory.parse_line(line)


def get_whenIO(source_file, default_time):
    kw = dict(default_time=default_time)
    line = source_file.next()
    if line.startswith('#'):
        line = line.lstrip('# ')
        timezone = line.split()[0]
        today = WhenIO(timezone).parse(line, toUTC=False)[0][0]
        whenIO = WhenIO(timezone, today, **kw)
    else:
        whenIO = WhenIO(**kw)
        source_file.seek(0)
    return whenIO


def yield_leaf(roots):
    goals = roots
    while goals:
        goal = goals.pop(0)
        if goal.children:
            goals.extend(goal.children)
            continue
        yield goal
