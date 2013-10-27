#!/usr/bin/env python
import datetime
import shutil
import sys
from tempfile import mkstemp
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE
from script import get_argument_parser, get_args


def run(source_paths, show_all, overwrite_first=False, target_timezone=None):
    if overwrite_first:
        temporary_path = mkstemp()[1]
        sys.stdout = open(temporary_path, 'wt')
    utcnow = datetime.datetime.utcnow()
    target_whenIO = WhenIO(timezone=target_timezone)
    print('# %s %s' % (
        target_whenIO._tz.zone,
        target_whenIO._today.strftime('%-m/%-d/%Y')))
    for source_path in source_paths:
        with open(source_path) as source_file:
            source_whenIO = load_whenIO(source_file)
            goal_factory = GoalFactory(source_whenIO)
            for line in source_file:
                goal = goal_factory.parse_line(line)
                if goal.status == STATUS_DONE and not goal.start:
                    goal.start = utcnow
                if show_all or goal.status < STATUS_DONE:
                    template = '%(leadspace)s%(status)s%(text)s%(when)s'
                    print(goal.format(template, whenIO=target_whenIO))
    if overwrite_first:
        sys.stdout.flush()
        shutil.move(temporary_path, source_paths[0])


if __name__ == '__main__':
    argument_parser = get_argument_parser()
    argument_parser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    argument_parser.add_argument(
        '-u', '--update', action='store_true',
        help='overwrite first file with output')
    args = get_args(argument_parser)
    run(args.source_paths, args.all, args.update, args.target_timezone)
