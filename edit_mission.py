#!/usr/bin/env python3
from argparse import ArgumentParser

from macros import call_editor
from models import Goal, GoalState, format_statistics, db
from routines import format_mission_text, parse_mission_text


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('goal_id', nargs='?')
    args = argument_parser.parse_args()
    goal_id = args.goal_id
    if not goal_id:
        goal = db.query(Goal).filter_by(
            state=GoalState.Pending).order_by(Goal.order).first()
    if goal_id or not goal:
        goal = Goal.get(goal_id)
    while True:
        mission_text = call_editor('goal.md', format_mission_text(goal))
        try:
            goals = parse_mission_text(mission_text)
        except ValueError:
            print('Mission required.')
        break
    for goal in goals:
        db.add(goal)
        db.commit()
    print(format_statistics())
