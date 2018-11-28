#!/usr/bin/env python3
import pytz
from argparse import ArgumentParser

from macros import call_editor
from models import Goal, GoalState, db
from routines import format_mission_text, format_summary, parse_mission_text
from settings import DEFAULT_TIMEZONE


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--timezone', '-T')
    argument_parser.add_argument('--all', '-A', action='store_true')
    argument_parser.add_argument('goal_id', nargs='?')
    args = argument_parser.parse_args()
    zone = pytz.timezone(args.timezone) if args.timezone else DEFAULT_TIMEZONE
    goal_id = args.goal_id
    if not goal_id:
        goal = db.query(Goal).filter_by(
            state=GoalState.Pending).order_by(Goal.order).first()
    if goal_id or not goal:
        goal = Goal.get(goal_id)
    while True:
        mission_text = call_editor('mission.md', format_mission_text(
            goal, zone, show_archived=args.all))
        try:
            goals = parse_mission_text(mission_text, zone)
        except ValueError:
            print('Mission required.')
        break
    for goal in goals:
        db.add(goal)
        db.commit()
    print(format_summary(zone))
