#!/usr/bin/env python
import argparse
import datetime
from tzlocal import get_localzone

from goalIO import GoalFactory, load_whenIO, STATUS_DONE


def run(sourcePaths, showAll):
    now = datetime.datetime.now()
    print '# %s %s' % (get_localzone(), now.strftime('%-m/%-d/%Y'))
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            whenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(whenIO)
            for line in sourceFile:
                goal = goalFactory.parse_line(line)
                if goal.status == STATUS_DONE and not goal.start:
                    goal.start = now
                if showAll or goal.status < STATUS_DONE:
                    print goal.format('%(leadspace)s%(status)s%(text)s%(when)s')


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+',
        help='text files with goals in hierarchical order')
    argumentParser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    arguments = argumentParser.parse_args()
    run(arguments.sourcePaths, arguments.all)
