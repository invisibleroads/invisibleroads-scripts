#!/usr/bin/env python3
from argparse import ArgumentParser

from macros import call_editor
from models import format_statistics, db
from routines import format_goal_text, parse_goal_text, get_goals


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--all', '-A', action='store_true')
    args = argument_parser.parse_args()
    goals = get_goals()
    goal_text = call_editor('goal.md', format_goal_text(
        goals, show_archived=args.all))
    for goal in parse_goal_text(goal_text):
        db.add(goal)
        db.commit()
    print(format_statistics())
