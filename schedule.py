#!/usr/bin/env python
import datetime
import sys
from collections import defaultdict
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE
from script import get_argumentParser


def run(sourcePaths, dayCount, timezone):
    goals = []
    targetWhenIO = WhenIO(timezone)
    # Parse
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            sourceWhenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(sourceWhenIO)
            for line in sourceFile:
                goals.append(goalFactory.parse_line(line))
    # Filter
    goals, warnings = filter_goals(goals, dayCount, targetWhenIO)
    # Format
    template = '%(time)s\t%(duration)s\t%(text)s'
    lines = format_schedule(goals, template, targetWhenIO)
    if lines:
        sys.stdout.write('\n'.join(lines) + '\n')
    # Analyze
    sys.stderr.write('\n'.join(warnings) + '\n')


def filter_goals(goals, dayCount, whenIO):
    selectedGoals = []
    countByDescription = defaultdict(int)
    timeLimit = whenIO._combine_date_time(
        whenIO._today + datetime.timedelta(days=dayCount + 1))
    for goal in goals:
        if not goal.duration:
            countByDescription['missing duration'] += 1
        if not goal.start:
            countByDescription['not scheduled'] += 1
            continue
        for selectedGoal in selectedGoals:
            if overlap(goal, selectedGoal):
                countByDescription['overlap'] += 1
                break
        start = whenIO._to_local(goal.start)
        if goal.status < STATUS_DONE and start < timeLimit:
            selectedGoals.append(goal)
    warnings = []
    if not selectedGoals:
        if dayCount == 0:
            timeRange = 'today'
        elif dayCount == 1:
            timeRange = 'tomorrow'
        else:
            timeRange = 'the next %s days' % dayCount
        warnings.append('Whoops! No goals scheduled for %s.' % timeRange)
    for description, count in countByDescription.iteritems():
        warnings.append('%s %s' % (count, description))
    return selectedGoals, warnings


def format_schedule(goals, template, whenIO):
    'Format in chronological order'
    lines = []
    currentDate = None
    for goal in sorted(goals, key=lambda _: _.start):
        start = whenIO._to_local(goal.start)
        if currentDate != start.date():
            if currentDate:
                lines.append('')
            currentDate = start.date()
            lines.append(whenIO.format_date(currentDate))
        lines.append(goal.format(template, omitStartDate=True, whenIO=whenIO))
    return lines


def overlap(goal1, goal2):
    latestStart = max(goal1.start, goal2.start)
    earliestEnd = min(goal1.start + goal1.duration,
                      goal2.start + goal2.duration)
    overlapInSeconds = (earliestEnd - latestStart).total_seconds() + 1
    return overlapInSeconds > 0


if __name__ == '__main__':
    argumentParser = get_argumentParser()
    argumentParser.add_argument(
        '-d', '--days', metavar='N', default=1, type=int,
        help='limit schedule by number of days from today')
    arguments = argumentParser.parse_args()
    run(arguments.sourcePaths,
        arguments.days,
        arguments.timezone)
