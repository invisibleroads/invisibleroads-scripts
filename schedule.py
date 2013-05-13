#!/usr/bin/env python
import datetime
import sys
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE
from script import get_argumentParser


def run(sourcePaths, showAll, dayCount, timezone):
    goals = []
    # Parse
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            sourceWhenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(sourceWhenIO)
            for line in sourceFile:
                goals.append(goalFactory.parse_line(line))
    # Output in chronological order
    text = format_schedule(goals, showAll, dayCount, timezone)
    if not text:
        if dayCount == 0:
            timeRange = 'today'
        elif dayCount == 1:
            timeRange = 'tomorrow'
        else:
            timeRange = 'the next %s days' % dayCount
        sys.stderr.write('Whoops! No goals scheduled for %s.' % timeRange)
        return ''
    return text


def format_schedule(goals, showAll, dayCount, timezone):
    'Format in chronological order'
    targetWhenIO = WhenIO(timezone)
    lines = []
    goals = filter(lambda _: _.start, goals)
    template = '%(time)s\t%(duration)s\t%(text)s'
    timeLimit = targetWhenIO._combine_date_time(
        targetWhenIO._today + datetime.timedelta(days=dayCount + 1))
    goals = filter(
        lambda _: targetWhenIO._to_local(_.start) < timeLimit, goals)
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
        lines.append(goal.format(
            template, omitStartDate=True, whenIO=targetWhenIO))
    return '\n'.join(lines)


if __name__ == '__main__':
    argumentParser = get_argumentParser()
    argumentParser.add_argument(
        '-a', '--all', action='store_true',
        help='show completed and cancelled goals too')
    argumentParser.add_argument(
        '-d', '--days', metavar='N', default=1, type=int,
        help='limit schedule by number of days from today')
    arguments = argumentParser.parse_args()
    print run(
        arguments.sourcePaths,
        arguments.all,
        arguments.days,
        arguments.timezone)
