#!/usr/bin/env python
import argparse
import datetime
from tzlocal import get_localzone
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE


def run(sourcePaths, showAll=False, dayCount=0, timezone=None):
    goals = []
    # Parse
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            sourceWhenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(sourceWhenIO)
            for line in sourceFile:
                goals.append(goalFactory.parse_line(line))
    # Output in chronological order
    targetWhenIO = WhenIO(timezone)
    lines = []
    goals = filter(lambda _: _.start, goals)
    template = '%(when_)s\t%(text)s'
    timeDelta = datetime.timedelta(days=dayCount + 1)
    timeLimit = targetWhenIO._combine_date_time(targetWhenIO._today + timeDelta)
    goals = filter(lambda _: targetWhenIO._to_local(_.start) < timeLimit, goals)
    if not showAll:
        goals = filter(lambda _: _.status < STATUS_DONE, goals)
    else:
        template = '%(statusSymbol)s ' + template
    currentDate = None
    for goal in sorted(goals, key=lambda _: _.start):
        start = targetWhenIO._to_local(goal.start)
        if currentDate != start.date():
            if currentDate:
                lines.append('')
            currentDate = start.date()
            lines.append(targetWhenIO.format_date(currentDate))
        lines.append(goal.format(template, omitStartDate=True, whenIO=targetWhenIO))
    if not lines:
        return 'Whoops! No goals scheduled until %s.' % targetWhenIO.format(
            timeLimit, fromUTC=False)
    return '\n'.join(lines)


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+', default='*.goals',
        help='text files with goals in hierarchical order')
    argumentParser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    argumentParser.add_argument(
        '-d', '--days', metavar='N', default=0, type=int,
        help='limit schedule by number of days from today')
    argumentParser.add_argument(
        '-t', '--timezone', metavar='TZ', default=get_localzone().zone,
        help='specify target timezone')
    arguments = argumentParser.parse_args()
    print run(
        arguments.sourcePaths,
        arguments.all,
        arguments.days,
        arguments.timezone)
