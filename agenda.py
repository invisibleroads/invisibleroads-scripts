#!/usr/bin/env python
import argparse
import datetime
from goalIO import GoalFactory, STATUS_DONE
from whenIO import WhenIO


whenIO = WhenIO()
# Parse arguments
argumentParser = argparse.ArgumentParser()
argumentParser.add_argument('sourcePaths', nargs='+')
argumentParser.add_argument('-d', '--days', type=int)
argumentParser.add_argument('-a', '--all', action='store_true')
arguments = argumentParser.parse_args()
# Parse goals
goals = []
goalFactory = GoalFactory(whenIO)
for sourcePath in arguments.sourcePaths:
    with open(sourcePath) as sourceFile:
        for line in sourceFile:
            goals.append(goalFactory.parse_line(line))
# Output goals in chronological order
goals = filter(lambda _: _.start, goals)
template = '%(whens)s\t%(text)s'
if arguments.days is not None:
    timeDelta = datetime.timedelta(days=arguments.days + 1)
    timeLimit = whenIO._combine_date_time(whenIO._today + timeDelta)
    goals = filter(lambda _: _.start < timeLimit, goals)
if not arguments.all:
    goals = filter(lambda _: _.status < STATUS_DONE, goals)
else:
    template = '%(statusSymbol)s ' + template
currentDate = None
for goal in sorted(goals, key=lambda _: _.start):
    if currentDate != goal.start.date():
        if currentDate:
            print
        currentDate = goal.start.date()
        print whenIO.format_date(currentDate)
    print goal.format(template, withStartDate=False)
