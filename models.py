import enum
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import DateTime, Enum, Integer, String


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

    def __repr__(self):
        return '%s(id=%s)' % (self.__class__.__name__, self.id)


class TextMixin(object):
    text = Column(String)
    text_datetime = Column(DateTime)


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

    @property
    def sorted_children(self):
        sorted_packs = sorted([
            (g.order, g) for g in self.children
        ], key=lambda _: _[0])
        return [_[1] for _ in sorted_packs]


class Note(IDMixin, TextMixin, Base):
    __tablename__ = 'note'
    goal_id = Column(String, ForeignKey('goal.id'))


engine = create_engine('sqlite:///goals.sqlite', echo=False)
Base.metadata.create_all(engine)
DatabaseSession = sessionmaker(bind=engine)
DatabaseSession.configure(bind=engine)
db = DatabaseSession()
