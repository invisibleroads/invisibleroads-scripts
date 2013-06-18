#!/usr/bin/env python
import datetime
import os
import pytz
import sys
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from whenIO import WhenIO

from goalIO import GoalFactory, load_whenIO, STATUS_DONE
from script import get_argumentParser, get_args, APPLICATION_NAME, CONFIG_NAME


def run(sourcePaths, dayCount, timezone):
    goals = []
    targetWhenIO = WhenIO(timezone)
    # Parse
    for sourcePath in sourcePaths:
        calendarName = get_calendarName(sourcePath)
        with open(sourcePath) as sourceFile:
            sourceWhenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(sourceWhenIO)
            for line in sourceFile:
                goal = goalFactory.parse_line(line)
                goal.calendar = calendarName
                goals.append(goal)
    goals, warnings = filter_goals(goals, dayCount, targetWhenIO)
    # Format
    template = '%(time)s\t%(duration)s\t%(text)s'
    lines = format_schedule(goals, template, targetWhenIO)
    if lines:
        sys.stdout.write('\n'.join(lines) + '\n')
    sys.stderr.write('\n'.join(warnings) + '\n')
    return goals


def get_calendarName(filePath):
    calendarName = os.path.splitext(filePath)[0]
    if 'todo' == calendarName.lower():
        folderPath = os.path.dirname(os.path.abspath(filePath))
        calendarName = os.path.basename(folderPath)
    return calendarName


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
    earliestEnd = min(goal1.start + (goal1.duration or relativedelta()),
                      goal2.start + (goal2.duration or relativedelta()))
    return (earliestEnd - latestStart).total_seconds() > 0


def get_service(configFolder, clientId, clientSecret, developerKey):
    from apiclient.discovery import build
    from httplib2 import Http
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client.file import Storage
    from oauth2client.tools import run as run_

    flow = OAuth2WebServerFlow(
        client_id=clientId, client_secret=clientSecret,
        scope='https://www.googleapis.com/auth/calendar',
        user_agent=APPLICATION_NAME)
    storagePath = os.path.join(configFolder, 'calendar.json')
    storage = Storage(storagePath)
    credentials = storage.get()
    if not credentials or credentials.invalid:
        credentials = run_(flow, storage)
    return build(
        serviceName='calendar', version='v3',
        http=credentials.authorize(Http()), developerKey=developerKey)


def synchronize(service, goals):
    idByName = make_calendars(set(x.calendar for x in goals))
    # Create events
    isoformat = lambda x: pytz.utc.localize(x).isoformat()
    for goal in goals:
        calendarId = idByName[goal.calendar]
        duration = goal.duration or datetime.timedelta(minutes=30)
        service.events().insert(calendarId=calendarId, body={
            'summary': goal.text,
            'start': {'dateTime': isoformat(goal.start)},
            'end': {'dateTime': isoformat(goal.start + duration)},
        }).execute()


def make_calendars(calendarNames):
    # Delete
    for item in service.calendarList().list().execute()['items']:
        if item['summary'] in calendarNames:
            service.calendarList().delete(calendarId=item['id']).execute()
    # Create
    idByName = {}
    for name in calendarNames:
        idByName[name] = service.calendars().insert(body={
            'summary': name,
        }).execute()['id']
    return idByName


if __name__ == '__main__':
    argumentParser = get_argumentParser()
    argumentParser.add_argument(
        '-d', '--days', metavar='DAYS', default=1, type=int,
        help='number of days to look ahead')
    argumentParser.add_argument(
        '-s', '--sync', action='store_true',
        help='synchronize with Google calendar')
    args = get_args(argumentParser)
    goals = run(args.sourcePaths, args.days, args.timezone)

    if goals and args.sync:
        if args.clientId:
            service = get_service(
                args.configFolder, args.clientId, args.clientSecret,
                args.developerKey)
            synchronize(service, goals)
        else:
            configPath = os.path.join(args.configFolder, CONFIG_NAME)
            print 'Parameters missing in %s:' % configPath
            print 'clientId, clientSecret, developerKey'
