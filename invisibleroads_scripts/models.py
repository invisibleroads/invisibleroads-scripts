import enum
import re
from datetime import datetime
from invisibleroads_macros.security import make_random_string
from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import DateTime, Enum, Integer, String

from .macros import (
    format_timestamp, parse_timestamp, sort_by_attribute, zone_datetime,
    UTC_TIMEZONE)
from .settings import ID_LENGTH, INDENT


INDENT_PATTERN = re.compile('^\\s+')
SEPARATOR = '# '
DATETIME = datetime.utcnow()
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
    id_datetime = Column(DateTime, default=DATETIME)

    @classmethod
    def get(Class, database, id):
        if id:
            instance = database.query(Class).get(id)
            if not instance:
                instance = Class(id=id)
            return instance
        else:
            while True:
                instance = Class(id=make_random_string(ID_LENGTH))
                database.add(instance)
                try:
                    database.flush()
                except IntegrityError:
                    database.rollback()

                break

            return instance

    def __repr__(self):
        return '%s(id=%s)' % (self.__class__.__name__, self.id)


class TextMixin(object):
    text = Column(String, default='')
    text_datetime = Column(DateTime)

    def set_text(self, text):
        if not hasattr(self, 'old_text'):
            self.old_text = self.text
        if text in (self.old_text, self.text):
            return
        self.text_datetime = DATETIME
        self.text = text.rstrip()

    def __repr__(self):
        return '%s(id=%s, text="%s")' % (
         self.__class__.__name__, self.id, self.text)


class Goal(TextMixin, IDMixin, Base):
    __tablename__ = 'goal'
    state = Column(Enum(GoalState), default=GoalState.Pending)
    state_datetime = Column(DateTime)
    schedule_datetime = Column(DateTime)
    order = Column(Integer, default=0)
    children = relationship(
        'Goal',
        secondary=GoalLink,
        primaryjoin='Goal.id == goal_link.c.parent_id',
        secondaryjoin='Goal.id == goal_link.c.child_id',
        backref='parents')
    notes = relationship('Note')

    def set_state(self, state):
        if not hasattr(self, 'old_state'):
            self.old_state = self.state
        if state in (self.old_state, self.state):
            return
        self.state_datetime = DATETIME
        self.state = state

    def set_schedule_date(self, date, zone):
        if date:
            old_utc_datetime = self.schedule_datetime
            if old_utc_datetime:
                old_local_datetime = zone_datetime(
                    old_utc_datetime, UTC_TIMEZONE, zone)
                new_local_datetime = datetime.combine(
                    date, old_local_datetime.time())
            else:
                new_local_datetime = date
            new_utc_datetime = zone_datetime(
                new_local_datetime, zone, UTC_TIMEZONE)
        else:
            new_utc_datetime = None
        self.schedule_datetime = new_utc_datetime

    @classmethod
    def parse_text(Class, database, text, zone):
        goal_text, _, meta_text = text.partition(SEPARATOR)
        goal_state = Class._parse_goal_state(goal_text)
        schedule_datetime, goal_id = Class._parse_meta_text(meta_text, zone)
        indent_depth = Class._parse_indent_depth(goal_text)
        goal = Goal.get(database, goal_id)
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
        elif text.startswith('+'):
            return GoalState.Done
        else:
            return GoalState.Pending

    @staticmethod
    def _parse_indent_depth(text):
        match = INDENT_PATTERN.match(text)
        if not match:
            return 0
        else:
            return len(match.group())

    @staticmethod
    def _parse_meta_text(text, zone):
        schedule_datetime, goal_id = (None, None)
        meta_terms = text.split()
        while meta_terms:
            meta_term = meta_terms.pop()
            try:
                schedule_datetime = parse_timestamp(meta_term, zone)
            except ValueError:
                if len(meta_term) == ID_LENGTH:
                    goal_id = meta_term

        return (
         schedule_datetime, goal_id)

    def render_text(self, zone, indent_depth=0):
        return '%s%s%s  %s%s' % (
         INDENT * indent_depth,
         PREFIX_BY_STATE[self.state],
         self.text,
         SEPARATOR,
         self._format_meta_text(zone))

    def _format_meta_text(self, zone):
        terms = []
        if self.schedule_datetime:
            terms.append(format_timestamp(self.schedule_datetime, zone))
        if self.notes:
            terms.append('...')
        terms.append(self.id)
        return (' ').join(terms)

    @property
    def sorted_notes(self):
        return sort_by_attribute(self.notes, 'id_datetime')


class Note(TextMixin, IDMixin, Base):
    __tablename__ = 'note'
    goal_id = Column(String, ForeignKey('goal.id'))

    def render_text(self, zone):
        return '%s  %s%s\n%s' % (
         format_timestamp(self.id_datetime, zone),
         SEPARATOR,
         self.id,
         self.text)


def get_database_from_configuration(configuration):
    database_url = get_database_url(configuration)
    return configure_database(database_url)


def configure_database(database_url):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    DatabaseSession = sessionmaker(bind=engine)
    DatabaseSession.configure(bind=engine)
    return DatabaseSession()


PREFIX_BY_STATE = {
    GoalState.Pending: '',
    GoalState.Cancelled: '_ ',
    GoalState.Done: '+ '}
