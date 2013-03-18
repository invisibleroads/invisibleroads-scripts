#!/usr/bin/env python
import argparse
import sys

from goalIO import GoalFactory, GoalError, load_whenIO, STATUS_NEXT, INDENT_UNIT


def run(sourcePaths):
    for sourcePath in sourcePaths:
        with open(sourcePath) as sourceFile:
            whenIO = load_whenIO(sourceFile)
            goalFactory = GoalFactory(whenIO)
            roots = goalFactory.parse_hierarchy(sourceFile)
            try:
                check_goals(roots)
            except GoalError, error:
                print error
                sys.exit(-1)
            goal = get_next_step(roots)
            if goal:
                print format_lineage(goal)
            else:
                print 'Whoops! We could not pinpoint the next step.'


def check_goals(goals):
    nextSteps = []
    for goal in goals:
        if STATUS_NEXT == goal.status:
            nextSteps.append(goal)
        if len(nextSteps) > 1:
            lines = ['Whoops! A goal can have at most one next step.']
            lines.append(INDENT_UNIT + nextSteps[0].text)
            lines.append(INDENT_UNIT + nextSteps[1].text)
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
    template = '%(leadspace)s%(text)s %(when)s'
    return '\n'.join(_.format(template) for _ in reversed(lineage))


if __name__ == '__main__':
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        'sourcePaths', nargs='+',
        help='text files with goals in hierarchical order')
    arguments = argumentParser.parse_args()
    run(arguments.sourcePaths)
