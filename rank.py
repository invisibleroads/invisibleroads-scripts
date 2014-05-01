from goalIO import GoalFactory, get_whenIO, yield_leaf
from script import get_argument_parser, get_args


GOAL_TEMPLATE = '%(duration)s\t%(text)s'


def run(source_paths, default_time):
    packs = []
    for source_path in source_paths:
        with open(source_path) as source_file:
            goal_factory = GoalFactory(
                get_whenIO(source_file, default_time=default_time))
            for goal in yield_leaf(goal_factory.parse_hierarchy(source_file)):
                absolute_impact = goal.absolute_impact
                if not absolute_impact:
                    continue
                packs.append((absolute_impact, -(goal.duration or 0), goal))
    for absolute_impact, duration, goal in sorted(packs, reverse=True):
        print '%s\t%s' % (absolute_impact, goal.format(GOAL_TEMPLATE))


if __name__ == '__main__':
    argument_parser = get_argument_parser()
    args = get_args(argument_parser)
    run(args.source_paths, args.default_time)
