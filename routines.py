import re
from collections import defaultdict
from datetime import datetime
from invisibleroads_macros.security import make_random_string
from invisibleroads_macros.timestamp import (
    format_timestamp, parse_timestamp, DATESTAMP_FORMAT)
from sqlalchemy.orm import joinedload

from models import Goal, GoalState, db


INDENT = '    '
INDENT_PATTERN = re.compile(r'^\s+')
META_SEPARATOR = ' # '


def get_goals():
    return db.query(Goal).options(
        joinedload(Goal.children),
        joinedload(Goal.parents),
    ).order_by(Goal.state, Goal.order).all()


def get_roots(goals):
    goal_ids = [g.id for g in goals]

    def has_parent(g):
        for parent in g.parents:
            if parent.id in goal_ids:
                return True
        return False

    roots = []
    for goal in goals:
        if not has_parent(goal):
            roots.append(goal)
    return roots


def format_goal_text(goals, show_archived=False):
    roots = get_roots(goals)
    lines = []
    for g in roots:
        lines.extend(format_goal_plan(g, depth=0, show_archived=show_archived))
    return '\n'.join(lines)


def format_schedule_text(goals, show_archived=False):
    goals_by_date = defaultdict(list)
    for g in goals:
        goal_datetime = g.schedule_datetime
        if not goal_datetime:
            continue
        goals_by_date[goal_datetime.date()].append(g)
    lines = []
    for goal_date in sorted(goals_by_date.keys()):
        goals = goals_by_date[goal_date]
        lines.append(goal_date.strftime(DATESTAMP_FORMAT))
        lines.extend([format_goal_line(g, depth=1) for g in goals])
    return '\n'.join(lines)


def format_goal_plan(goal, depth, show_archived):
    if not show_archived:
        if goal.state in [GoalState.Cancelled, GoalState.Done]:
            return []
    lines = [format_goal_line(goal, depth)]
    for child in goal.sorted_children:
        lines.extend(format_goal_plan(child, depth + 1, show_archived))
    return lines


def format_goal_line(goal, depth):
    return '%s%s%s %s%s' % (
        INDENT * depth,
        format_goal_state(goal),
        goal.text,
        META_SEPARATOR,
        format_meta_text(goal))


def format_goal_state(goal):
    goal_state = goal.state
    if goal_state == GoalState.Cancelled:
        return '_ '
    if goal_state == GoalState.Done:
        return '+ '
    return ''


def format_meta_text(goal):
    meta_terms = []
    if goal.schedule_datetime:
        schedule_timestamp = format_timestamp(goal.schedule_datetime)
        meta_terms.append(schedule_timestamp)
    meta_terms.append(goal.id)
    return ' '.join(meta_terms)


def parse_goal_text(text):
    goals = []
    parent_by_depth = {}
    order = 0
    for line in text.splitlines():
        goal = parse_goal_line(line)
        goal_parent = get_parent(goal.depth, parent_by_depth)
        if not hasattr(goal, 'explicit_parents'):
            goal.explicit_parents = []
        if goal_parent:
            goal.explicit_parents.append(goal_parent)
        goal.order = order
        update_parent_by_depth(goal, goal.depth, parent_by_depth)
        goals.append(goal)
        order += 1
    goal_ids = [g.id for g in goals]
    for g in goals:
        g.implicit_parents = []
        for parent in g.parents:
            if parent.id in goal_ids:
                continue
            g.implicit_parents.append(parent)
        g.parents = g.explicit_parents + g.implicit_parents
    return goals


def parse_schedule_text(text):
    goals = []
    goal_date = None
    for line in text.splitlines():
        line = line.strip()
        try:
            goal_date = parse_timestamp(line)
        except ValueError:
            pass
        else:
            continue
        goal = parse_goal_line(line)
        goal_datetime = goal.schedule_datetime
        goal.schedule_datetime = goal_date.replace(
            hour=goal_datetime.hour,
            minute=goal_datetime.minute)
        goals.append(goal)
    return goals


def parse_goal_line(text):
    goal_text, _, meta_text = text.partition(META_SEPARATOR)
    goal_state = parse_goal_state(goal_text)
    goal_depth = parse_goal_depth(goal_text)
    schedule_datetime, goal_id = parse_meta_text(meta_text)
    if goal_id:
        goal = db.query(Goal).get(goal_id)
    else:
        goal = Goal(id=make_random_string(7))
    goal_text = goal_text.lstrip(' _+').rstrip()
    if goal.text != goal_text:
        goal.text_datetime = datetime.utcnow()
    if goal.state != goal_state:
        goal.state_datetime = datetime.utcnow()
    goal.text = goal_text
    goal.state = goal_state
    goal.depth = goal_depth
    goal.schedule_datetime = schedule_datetime
    return goal


def parse_goal_state(text):
    text = text.lstrip()
    if text.startswith('_'):
        return GoalState.Cancelled
    if text.startswith('+'):
        return GoalState.Done
    return GoalState.Pending


def parse_goal_depth(text):
    match = INDENT_PATTERN.match(text)
    if not match:
        return 0
    return len(match.group())


def parse_meta_text(text):
    schedule_datetime, goal_id = None, None
    meta_terms = text.split()
    while meta_terms:
        meta_term = meta_terms.pop()
        try:
            schedule_datetime = parse_timestamp(meta_term)
        except ValueError:
            goal_id = meta_term
    return schedule_datetime, goal_id


def get_parent(goal_depth, parent_by_depth):
    best_depth = -1
    best_parent = None
    for depth, parent in parent_by_depth.items():
        if goal_depth > depth and depth > best_depth:
            best_depth = depth
            best_parent = parent
    return best_parent


def update_parent_by_depth(goal, goal_depth, parent_by_depth):
    bad_depths = []
    for depth, parent in parent_by_depth.items():
        if depth > goal_depth:
            bad_depths.append(depth)
            continue
    for depth in bad_depths:
        del parent_by_depth[depth]
    parent_by_depth[goal_depth] = goal
