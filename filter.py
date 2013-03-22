#!/usr/bin/env python
import argparse
import datetime
import shutil
import sys
from tempfile import mkstemp
from tzlocal import get_localzone
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE


def run(sourcePaths, showAll, overwriteFirst=False):
    if overwriteFirst:
        temporaryPath = mkstemp()[1]
        sys.stdout = open(temporaryPath, 'wt')
    now = datetime.datetime.now()
    print '# %s %s' % (get_localzone(), now.strftime('%-m/%-d/%Y'))
    whenIO = WhenIO(today=now)
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            goalFactory = GoalFactory(load_whenIO(sourceFile))
            for line in sourceFile:
                goal = goalFactory.parse_line(line)
                if goal.status == STATUS_DONE and not goal.start:
                    goal.start = now
                if showAll or goal.status < STATUS_DONE:
                    template = '%(leadspace)s%(status)s%(text)s%(when)s'
                    print goal.format(template, whenIO=whenIO)
    if overwriteFirst:
        sys.stdout.flush()
        shutil.move(temporaryPath, sourcePaths[0])


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+',
        help='text files with goals in hierarchical order')
    argumentParser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    argumentParser.add_argument(
        '-u', '--update', action='store_true',
        help='overwrite first file with output')
    arguments = argumentParser.parse_args()
    run(arguments.sourcePaths, arguments.all, arguments.update)
