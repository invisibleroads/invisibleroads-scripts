#!/usr/bin/env python
import sys

from goalIO import (
    GoalFactory,
    GoalError,
    load_whenIO,
    STATUS_NEXT,
    INDENT_UNIT)
from script import get_argument_parser, get_args


def run(source_paths):
    print_line = lambda _: sys.stdout.write(_ + '\n')
    print_error = lambda _: sys.stderr.write(_ + '\n')
    for source_path in source_paths:
        with open(source_path) as source_file:
            whenIO = load_whenIO(source_file)
            goal_factory = GoalFactory(whenIO)
            roots = goal_factory.parse_hierarchy(source_file)
            try:
                check_goals(roots)
            except GoalError, error:
                print_error(str(error))
                sys.exit(-1)
            goal = get_next_step(roots)
            if goal:
                print_line(format_lineage(goal))
            else:
                print_error('Whoops! We could not pinpoint the next step.')


def check_goals(goals):
    next_steps = []
    for goal in goals:
        if STATUS_NEXT == goal.status:
            next_steps.append(goal)
        if len(next_steps) > 1:
            lines = ['Whoops! A goal can have at most one next step.']
            lines.append(INDENT_UNIT + next_steps[0].text)
            lines.append(INDENT_UNIT + next_steps[1].text)
            raise GoalError('\n'.join(lines))
        check_goals(goal.children)


def get_next_step(goals):
    for goal in goals:
        if STATUS_NEXT == goal.status:
            if goal.children:
                return get_next_step(goal.children)
            else:
                return goal


def format_lineage(goal):
    lineage = [goal]
    while goal.parent:
        lineage.append(goal.parent)
        goal = goal.parent
    template = '%(leadspace)s%(text)s%(when)s'
    return '\n'.join(_.format(template) for _ in reversed(lineage))


if __name__ == '__main__':
    argument_parser = get_argument_parser()
    args = get_args(argument_parser)
    run(args.source_paths)
