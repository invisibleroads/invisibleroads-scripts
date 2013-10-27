from datetime import datetime
from dateutil.relativedelta import relativedelta
from unittest import TestCase

from goalIO import GoalFactory


TEXT = """\
    1
      11

      12

  2

    21
      211
"""


class TestGoalFactory(TestCase):

    def setUp(self):
        self.goal_factory = GoalFactory(in_utc=False)

    def test_parse_line(self):
        def expect(line, text, start, duration):
            goal = self.goal_factory.parse_line(line)
            self.assertEqual(goal.text, text)
            self.assertEqual(goal.start, start)
            self.assertEqual(goal.duration, duration)
        expect(
            'be  free  [1/1/2000 12am 1am]',
            text='be free',
            start=datetime(2000, 1, 1),
            duration=relativedelta(hours=1))
        expect(
            'run [30m]',
            text='run',
            start=None,
            duration=relativedelta(minutes=30))

    def test_parse_hierarchy(self):
        roots = self.goal_factory.parse_hierarchy(TEXT.splitlines())
        self.assertEqual('1', roots[0].text)
        self.assertEqual('11', roots[0].children[0].text)
        self.assertEqual('12', roots[0].children[1].text)
        self.assertEqual('2', roots[1].text)
        self.assertEqual('21', roots[1].children[0].text)
        self.assertEqual('211', roots[1].children[0].children[0].text)
