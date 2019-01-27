from argparse import ArgumentParser
from collections import defaultdict
from configparser import ConfigParser
from invisibleroads_scripts.models import (
    Goal, GoalLink, get_database_from_configuration)
from invisibleroads_scripts.routines import get_roots
from invisibleroads_scripts.settings import CONFIGURATION_PATH


a = ArgumentParser()
a.add_argument(
    '--configuration_path', '-C', metavar='PATH', default=CONFIGURATION_PATH)
args = a.parse_args()
c = ConfigParser()
c.read(args.configuration_path)
database = get_database_from_configuration(c)
goals = database.query(Goal).all()
goals = get_roots(goals)
count_by_id = defaultdict(int)
bad_goals = []
while goals:
    goal = goals.pop()
    if count_by_id.get(goal.id, 0) > 3:
        bad_goals.append(goal)
        continue
    goals.extend(goal.children)
    count_by_id[goal.id] += 1
for goal in bad_goals:
    database.execute(
        GoalLink.delete().where(GoalLink.c.parent_id == goal.id))
    database.execute(
        GoalLink.delete().where(GoalLink.c.child_id == goal.id))
database.commit()
