#!/usr/bin/env python3
import pytz
from argparse import ArgumentParser

from macros import call_editor
from models import db, backup_database
from routines import (
    format_schedule_text, format_summary, get_goals, parse_schedule_text)
from settings import DEFAULT_TIMEZONE


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--timezone', '-T')
    argument_parser.add_argument('--all', '-A', action='store_true')
    args = argument_parser.parse_args()
    zone = pytz.timezone(args.timezone) if args.timezone else DEFAULT_TIMEZONE
    goals = get_goals()
    goal_text = call_editor('schedule.md', format_schedule_text(
        goals, zone, args.all))
    for goal in parse_schedule_text(goal_text, zone):
        db.add(goal)
        db.commit()
    print('backup_path = %s' % backup_database(zone))
    print(format_summary(zone))
