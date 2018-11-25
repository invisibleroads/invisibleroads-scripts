import enum
import re
from datetime import datetime
from invisibleroads_macros.security import make_random_string
from invisibleroads_macros.timestamp import format_timestamp, parse_timestamp
from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import DateTime, Enum, Integer, String

from macros import sort_by_attribute
from settings import DATABASE_PATH, ID_LENGTH


INDENT = '    '
INDENT_PATTERN = re.compile(r'^\s+')
SEPARATOR = '# '


Base = declarative_base()
GoalLink = Table(
    'goal_link', Base.metadata,
    Column('parent_id', String, ForeignKey('goal.id')),
    Column('child_id', String, ForeignKey('goal.id')))


class GoalState(enum.IntEnum):
    Pending = 0
    Cancelled = -1
    Done = 1


class IDMixin(object):
    id = Column(String, primary_key=True)
    id_datetime = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def get(Class, id):
        if id:
            instance = db.query(Class).get(id)
            if not instance:
                instance = Class(id=id)
        else:
            instance = Class(id=make_random_string(ID_LENGTH))
        return instance

    def __repr__(self):
        return '%s(id=%s)' % (self.__class__.__name__, self.id)


class TextMixin(object):
    text = Column(String)
    text_datetime = Column(DateTime)

    def set_text(self, text):
        if self.text != text:
            self.text_datetime = datetime.utcnow()
        self.text = text.strip()


class Goal(IDMixin, TextMixin, Base):
    __tablename__ = 'goal'
    state = Column(Enum(GoalState), default=GoalState.Pending)
    state_datetime = Column(DateTime)
    schedule_datetime = Column(DateTime)
    order = Column(Integer, default=0)
    children = relationship(
        'Goal', secondary=GoalLink,
        primaryjoin='Goal.id == goal_link.c.parent_id',
        secondaryjoin='Goal.id == goal_link.c.child_id',
        backref='parents')
    notes = relationship('Note')

    def set_state(self, state):
        if self.state != state:
            self.state_datetime = datetime.utcnow()
        self.state = state

    @classmethod
    def parse_text(Class, text):
        goal_text, _, meta_text = text.partition(SEPARATOR)
        goal_state = Class._parse_goal_state(goal_text)
        schedule_datetime, goal_id = Class._parse_meta_text(meta_text)
        indent_depth = Class._parse_indent_depth(goal_text)
        goal = Goal.get(goal_id)
        goal.set_text(goal_text.lstrip(' _+'))
        goal.set_state(goal_state)
        goal.schedule_datetime = schedule_datetime
        goal.indent_depth = indent_depth
        return goal

    @staticmethod
    def _parse_goal_state(text):
        text = text.lstrip()
        if text.startswith('_'):
            return GoalState.Cancelled
        if text.startswith('+'):
            return GoalState.Done
        return GoalState.Pending

    @staticmethod
    def _parse_indent_depth(text):
        match = INDENT_PATTERN.match(text)
        if not match:
            return 0
        return len(match.group())

    @staticmethod
    def _parse_meta_text(text):
        schedule_datetime, goal_id = None, None
        meta_terms = text.split()
        while meta_terms:
            meta_term = meta_terms.pop()
            try:
                schedule_datetime = parse_timestamp(meta_term)
            except ValueError:
                if len(meta_term) == ID_LENGTH:
                    goal_id = meta_term
        return schedule_datetime, goal_id

    def render_text(self, indent_depth=0):
        return '%s%s%s  %s%s' % (
            INDENT * indent_depth,
            self.prefix,
            self.text or 'Set a goal',
            SEPARATOR,
            self.suffix)

    @property
    def prefix(self):
        goal_state = self.state
        if goal_state == GoalState.Cancelled:
            return '_ '
        if goal_state == GoalState.Done:
            return '+ '
        return ''

    @property
    def suffix(self):
        terms = []
        if self.schedule_datetime:
            terms.append(format_timestamp(self.schedule_datetime))
        if self.notes:
            terms.append('...')
        terms.append(self.id)
        return ' '.join(terms)

    @property
    def sorted_notes(self):
        return sort_by_attribute(self.notes, 'id_datetime')

    @property
    def sorted_children(self):
        return sort_by_attribute(self.children, 'order')


class Note(IDMixin, TextMixin, Base):
    __tablename__ = 'note'
    goal_id = Column(String, ForeignKey('goal.id'))

    def render_text(self):
        return '%s  %s%s\n%s' % (
            format_timestamp(self.id_datetime),
            SEPARATOR,
            self.id,
            self.text)


engine = create_engine('sqlite:///%s' % DATABASE_PATH, echo=False)
Base.metadata.create_all(engine)
DatabaseSession = sessionmaker(bind=engine)
DatabaseSession.configure(bind=engine)
db = DatabaseSession()
