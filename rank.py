#!/usr/bin/env python
from dateutil.relativedelta import relativedelta
from goalIO import GoalFactory, get_whenIO, yield_leaf, STATUS_DONE
from script import get_argument_parser, get_args


GOAL_TEMPLATE = '%(duration)s\t%(text)s'


def run(source_paths, default_time, maximum_count, verbose):
    packs = []
    for source_path in source_paths:
        with open(source_path) as source_file:
            goal_factory = GoalFactory(
                get_whenIO(source_file, default_time=default_time))
            for goal in yield_leaf(goal_factory.parse_hierarchy(source_file)):
                absolute_impact = goal.absolute_impact
                if goal.status >= STATUS_DONE:
                    continue
                if not absolute_impact:
                    if verbose:
                        print 'Missing impact: %s' % goal.format()
                    continue
                effort = get_effort(goal.duration)
                score = absolute_impact / float(effort)
                packs.append((score, goal))
    for score, goal in sorted(packs, reverse=True)[:maximum_count]:
        print '%s\t%s' % (
            goal.absolute_impact,
            goal.format(GOAL_TEMPLATE))


def get_effort(duration):
    if not duration:
        return get_effort(relativedelta(hours=2))
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
    argument_parser.add_argument(
        '-n', metavar='COUNT', type=int, default=10,
        help='maximum number of goals to show')
    args = get_args(argument_parser)
    run(args.source_paths, args.default_time, args.n, args.verbose)
