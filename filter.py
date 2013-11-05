#!/usr/bin/env python
import datetime
import os
import sys
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE
from script import get_argument_parser, get_args


GOAL_TEMPLATE = '%(leadspace)s%(status)s%(text)s%(when)s'


def run(source_paths, show_all, overwrite=False, target_timezone=None):
    target_whenIO = WhenIO(timezone=target_timezone)
    header = '# %s %s' % (
        target_whenIO._tz.zone,
        target_whenIO._today.strftime('%-m/%-d/%Y'))
    for source_path in source_paths:
        with Output(source_path, overwrite) as output:
            output.write(header)
            with open(source_path) as source_file:
                process(source_file, output, show_all, target_whenIO)


def process(source_file, output, show_all, target_whenIO):
    utcnow = datetime.datetime.utcnow()
    archived_goals = []
    goal_factory = GoalFactory(load_whenIO(source_file))
    for line in source_file:
        goal = goal_factory.parse_line(line)
        if goal.status == STATUS_DONE and not goal.start:
            goal.start = utcnow
        if show_all or goal.status < STATUS_DONE:
            output.write(goal.format(
                GOAL_TEMPLATE, whenIO=target_whenIO))
        if goal.status == STATUS_DONE:
            archived_goals.append(goal)
    for goal in sorted(archived_goals, key=lambda x: x.start, reverse=True):
        output.log(' '.join([
            goal.format('%(status)s%(text)s'),
            '[%s]' % utcnow.strftime('%m/%d/%Y'),
        ]))


class Output(object):

    def __init__(self, source_path, overwrite):
        self.source_path = source_path
        self.overwrite = overwrite

    def __enter__(self):
        self.target_lines = []
        self.log_lines = []
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.overwrite:
            self.overwrite_source()
            self.update_log()

    def write(self, text):
        self.target_lines.append(text)

    def log(self, text):
        self.log_lines.append(text)

    def overwrite_source(self):
        open(self.source_path, 'wt').write('\n'.join(self.target_lines))

    def update_log(self):
        lines = [
            '# UTC %s' % datetime.datetime.utcnow().strftime('%m/%d/%Y'),
        ] + self.log_lines
        log_path = os.path.splitext(self.source_path)[0] + '.log'
        try:
            for line in open(log_path, 'rt'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                lines.append(line)
        except IOError:
            pass
        open(log_path, 'wt').write('\n'.join(lines))


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
