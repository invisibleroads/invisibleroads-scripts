#!/usr/bin/env python3
import pytz
from argparse import ArgumentParser

from macros import call_editor
from models import db
from routines import (
    format_goal_text, format_summary, get_goals, parse_goal_text)
from settings import DEFAULT_TIMEZONE


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--timezone', '-T')
    argument_parser.add_argument('--all', '-A', action='store_true')
    args = argument_parser.parse_args()
    zone = pytz.timezone(args.timezone) if args.timezone else DEFAULT_TIMEZONE
    goals = get_goals()
    goal_text = call_editor('goal.md', format_goal_text(
        goals, zone, show_archived=args.all))
    for goal in parse_goal_text(goal_text, zone):
        db.add(goal)
        db.commit()
    print(format_summary(zone))
