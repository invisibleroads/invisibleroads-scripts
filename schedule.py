#!/usr/bin/env python
import datetime
import os
import pytz
import sys
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from whenIO import WhenIO

from goalIO import yield_goal, STATUS_DONE
from script import get_argument_parser, get_args, APPLICATION_NAME, CONFIG_NAME


def run(source_paths, default_time, day_count, target_timezone, verbose):
    goals = []
    target_whenIO = WhenIO(target_timezone)
    # Parse
    for source_path in source_paths:
        calendar_name = get_calendar_name(source_path)
        for goal in yield_goal(source_path, default_time):
            goal.calendar = calendar_name
            goals.append(goal)
    goals, warnings = filter_goals(goals, day_count, target_whenIO, verbose)
    # Format
    template = '%(time)s\t%(duration)s\t%(text)s'
    lines = format_schedule(goals, template, target_whenIO)
    if lines:
        sys.stdout.write('\n'.join(lines) + '\n')
    sys.stderr.write('\n'.join(warnings) + '\n')
    return goals


def get_calendar_name(file_path):
    calendar_name = os.path.splitext(file_path)[0]
    if 'todo' == calendar_name.lower():
        folder_path = os.path.dirname(os.path.abspath(file_path))
        calendar_name = os.path.basename(folder_path)
    return calendar_name


def filter_goals(goals, day_count, whenIO, verbose):
    selected_goals = []
    count_by_description = defaultdict(int)
    time_limit = whenIO._combine_date_time(
        whenIO._today + datetime.timedelta(days=day_count + 1))
    for goal in goals:
        if not goal.duration:
            if verbose:
                print('Missing duration: %s' % goal.format())
            count_by_description['missing duration'] += 1
        if not goal.start:
            if verbose:
                print('Not scheduled: %s' % goal.format())
            count_by_description['not scheduled'] += 1
            continue
        for selected_goal in selected_goals:
            if overlap(goal, selected_goal):
                count_by_description['overlap'] += 1
                break
        start = whenIO._to_local(goal.start)
        if goal.status < STATUS_DONE and start < time_limit:
            selected_goals.append(goal)
    warnings = []
    if not selected_goals:
        if day_count == 0:
            time_range = 'today'
        elif day_count == 1:
            time_range = 'tomorrow'
        else:
            time_range = 'the next %s days' % day_count
        warnings.append('Whoops! No goals scheduled for %s.' % time_range)
    for description, count in count_by_description.items():
        warnings.append('%s %s' % (count, description))
    return selected_goals, warnings


def format_schedule(goals, template, whenIO):
    'Format in chronological order'
    lines = []
    current_date = None
    for goal in sorted(goals, key=lambda _: _.start):
        start = whenIO._to_local(goal.start)
        if current_date != start.date():
            if current_date:
                lines.append('')
            current_date = start.date()
            lines.append(whenIO.format_date(current_date))
        lines.append(goal.format(
            template, omit_start_date=True, whenIO=whenIO))
    return lines


def overlap(goal1, goal2):
    latest_start = max(goal1.start, goal2.start)
    earliest_end = min(goal1.start + (goal1.duration or relativedelta()),
                       goal2.start + (goal2.duration or relativedelta()))
    return (earliest_end - latest_start).total_seconds() > 0


def get_service(
        config_folder, client_id, client_secret, developer_key, user_email):
    from apiclient.discovery import build
    from httplib2 import Http
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client.file import Storage
    from oauth2client.tools import run as run_

    flow = OAuth2WebServerFlow(
        client_id=client_id, client_secret=client_secret,
        scope='email https://www.googleapis.com/auth/calendar',
        user_agent=APPLICATION_NAME)
    storage_path = os.path.join(config_folder, user_email or 'default.json')
    storage = Storage(storage_path)
    credentials = storage.get()
    if not credentials or credentials.invalid:
        credentials = run_(flow, storage)
    # Save credentials
    client_email = credentials.token_response['id_token']['email']
    credential_path = os.path.join(config_folder, client_email)
    open(credential_path, 'w').write(credentials.to_json())
    # Return service
    return build(
        serviceName='calendar', version='v3',
        http=credentials.authorize(Http()), developerKey=developer_key)


def synchronize(service, goals):
    calendar_names = set(x.calendar for x in goals)
    calendar_id_by_name = make_calendars(service, calendar_names)
    clear_events(service, calendar_id_by_name.values())
    # Make events
    isoformat = lambda x: pytz.utc.localize(x).isoformat()
    for goal in goals:
        calendar_id = calendar_id_by_name[goal.calendar]
        duration = goal.duration or datetime.timedelta(minutes=30)
        service.events().insert(calendarId=calendar_id, body={
            'summary': goal.text,
            'start': {'dateTime': isoformat(goal.start)},
            'end': {'dateTime': isoformat(goal.start + duration)},
        }).execute()
    return calendar_id_by_name


def make_calendars(service, calendar_names):
    calendar_id_by_name = {}
    for calendar_item in service.calendarList().list().execute()['items']:
        calendar_name = calendar_item['summary']
        if calendar_name in calendar_names:
            calendar_id = calendar_item['id']
            calendar_id_by_name[calendar_name] = calendar_id
    for calendar_name in calendar_names:
        if calendar_name not in calendar_id_by_name:
            calendar_id_by_name[calendar_name] = service.calendars().insert(
                body={'summary': calendar_name}).execute()['id']
    return calendar_id_by_name


def clear_events(service, calendar_ids):
    for calendar_id in calendar_ids:
        for event_item in service.events().list(
            calendarId=calendar_id
        ).execute()['items']:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_item['id'],
            ).execute()


def clone_acls(service, calendar_names):
    primary_calendar = get_primary_calendar(service)
    primary_acls = service.acl().list(
        calendarId=primary_calendar['id'],
    ).execute()['items']
    secondary_acls = filter(lambda x: x['role'] != 'owner', primary_acls)
    for calendar in service.calendarList().list().execute()['items']:
        if calendar['summary'] not in calendar_names:
            continue
        for acl in secondary_acls:
            service.acl().insert(
                calendarId=calendar['id'],
                body={'role': acl['role'], 'scope': acl['scope']},
            ).execute()


def get_primary_calendar(service):
    for calendar in service.calendarList().list().execute()['items']:
        if 'primary' in calendar:
            return calendar


if __name__ == '__main__':
    argument_parser = get_argument_parser()
    argument_parser.add_argument(
        '-d', '--days', metavar='DAYS',
        default=2, type=int,
        help='number of days to look ahead')
    argument_parser.add_argument(
        '-s', '--synchronize', metavar='EMAIL', nargs='?',
        default=False, const=True,
        help='synchronize calendar and clone permissions')
    args = get_args(argument_parser)
    goals = run(
        args.source_paths, args.default_time, args.days, args.target_timezone,
        args.verbose)
    if goals and args.synchronize:
        if not args.client_id:
            config_path = os.path.join(args.config_folder, CONFIG_NAME)
            print('Parameters missing in %s:' % config_path)
            print('client_id, client_secret, developer_key')
        try:
            user_email = args.synchronize if '@' in args.synchronize else ''
        except TypeError:
            user_email = ''
        service = get_service(
            args.config_folder, args.client_id, args.client_secret,
            args.developer_key, user_email)
        calendar_id_by_name = synchronize(service, goals)
        clone_acls(service, calendar_id_by_name)
