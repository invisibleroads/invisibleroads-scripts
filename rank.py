#!/usr/bin/env python
from dateutil.relativedelta import relativedelta
from goalIO import GoalFactory, get_whenIO, yield_leaf
from script import get_argument_parser, get_args


GOAL_TEMPLATE = '%(duration)s\t%(text)s'


def run(source_paths, default_time):
    packs = []
    hard_goals = []
    HOUR_EFFORT = get_effort(relativedelta(hours=1))
    for source_path in source_paths:
        with open(source_path) as source_file:
            goal_factory = GoalFactory(
                get_whenIO(source_file, default_time=default_time))
            for goal in yield_leaf(goal_factory.parse_hierarchy(source_file)):
                absolute_impact = goal.absolute_impact
                if not absolute_impact:
                    continue
                effort = get_effort(goal.duration)
                if effort > HOUR_EFFORT:
                    hard_goals.append(goal)
                score = absolute_impact / float(effort)
                packs.append((score, goal))
    if hard_goals:
        print 'Whoops! Please split these goals into smaller steps.'
        for goal in hard_goals:
            print '\t%s' % goal.format(GOAL_TEMPLATE)
        return
    for score, goal in sorted(packs, reverse=True):
        print '%s\t%s' % (
            goal.absolute_impact,
            goal.format(GOAL_TEMPLATE))


def get_effort(duration):
    if not duration:
        return get_effort(relativedelta(days=1))
    convert_microseconds = lambda microseconds: microseconds
    convert_seconds = lambda seconds: seconds * 1000000
    convert_minutes = lambda minutes: convert_seconds(minutes * 60)
    convert_hours = lambda hours: convert_minutes(hours * 60)
    convert_days = lambda days: convert_hours(days * 24)
    convert_months = lambda months: convert_days(months * 30.436875)
    convert_years = lambda years: convert_months(years * 12)
    effort = sum([
        convert_microseconds(duration.microseconds),
        convert_seconds(duration.seconds),
        convert_minutes(duration.minutes),
        convert_hours(duration.hours),
        convert_days(duration.days + duration.leapdays),
        convert_months(duration.months),
        convert_years(duration.years),
    ])
    return effort


if __name__ == '__main__':
    argument_parser = get_argument_parser()
    args = get_args(argument_parser)
    run(args.source_paths, args.default_time)
