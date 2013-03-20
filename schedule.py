#!/usr/bin/env python
import argparse
import datetime
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE


def run(sourcePaths, showAll=False, dayCount=0):
    goals = []
    # Parse
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            goalFactory = GoalFactory(load_whenIO(sourceFile))
            for line in sourceFile:
                goals.append(goalFactory.parse_line(line))
    # Output in chronological order
    whenIO = WhenIO()
    lines = []
    goals = filter(lambda _: _.start, goals)
    template = '%(when_)s\t%(text)s'
    timeDelta = datetime.timedelta(days=dayCount + 1)
    timeLimit = whenIO._combine_date_time(whenIO._today + timeDelta)
    goals = filter(lambda _: _.start < timeLimit, goals)
    if not showAll:
        goals = filter(lambda _: _.status < STATUS_DONE, goals)
    else:
        template = '%(statusSymbol)s ' + template
    currentDate = None
    for goal in sorted(goals, key=lambda _: _.start):
        if currentDate != goal.start.date():
            if currentDate:
                lines.append('')
            currentDate = goal.start.date()
            lines.append(whenIO.format_date(currentDate))
        lines.append(goal.format(template, omitStartDate=True))
    if not lines:
        return 'Whoops! No goals scheduled until %s.' % whenIO.format(timeLimit, fromUTC=False)
    return '\n'.join(lines)


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+',
        help='text files with goals in hierarchical order')
    argumentParser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    argumentParser.add_argument(
        '-d', '--days', type=int, default=0,
        help='limit agenda by number of days from today')
    arguments = argumentParser.parse_args()
    print run(arguments.sourcePaths, arguments.all, arguments.days)
