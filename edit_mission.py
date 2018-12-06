#!/usr/bin/env python3
import pytz
from argparse import ArgumentParser

from macros import call_editor
from models import db, backup_database
from routines import (
    format_mission_text, format_summary, get_goals, parse_mission_text)
from settings import DEFAULT_TIMEZONE


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--timezone', '-T')
    argument_parser.add_argument('--all', '-A', action='store_true')
    argument_parser.add_argument('terms', nargs='*')
    args = argument_parser.parse_args()
    zone = pytz.timezone(args.timezone) if args.timezone else DEFAULT_TIMEZONE
    terms = args.terms
    goals = get_goals(terms)
    while True:
        mission_text = call_editor('mission.md', format_mission_text(
            goals, zone, show_archived=args.all))
        try:
            goals = parse_mission_text(mission_text, zone)
        except ValueError:
            print('Mission required.')
        break
    for goal in goals:
        db.add(goal)
        db.commit()
    print('backup_path = %s' % backup_database(zone))
    print(format_summary(zone))
