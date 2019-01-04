import networkx as nx
from collections import defaultdict
from datetime import datetime
from invisibleroads_macros.disk import make_folder
from os.path import join
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from .macros import (
    parse_text_by_key, parse_timestamp, sort_by_attribute,
    zone_datetime, DATESTAMP_FORMAT, UTC_TIMEZONE)
from .models import Goal, GoalCache, GoalState, Note, SEPARATOR


def get_goals(database, terms=None, with_notes=False):
    goal_query = database.query(Goal)
    if terms:
        text_expressions = [Goal.id.in_(terms)]
        for term in terms:
            text_expressions.append(Goal.text.ilike('%' + term + '%'))
        if text_expressions:
            goal_query = goal_query.filter(or_(*text_expressions))
    if with_notes:
        goal_query = goal_query.options(joinedload(Goal.notes))
    return goal_query.options(
        joinedload(Goal.children),
        joinedload(Goal.parents),
    ).order_by(
        Goal.state,
        Goal.order).all()


def get_roots(goals=None):
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


def get_parent(goal_depth, parent_by_indent_depth):
    best_depth = -1
    best_parent = None
    for indent_depth, parent in parent_by_indent_depth.items():
        if goal_depth > indent_depth and indent_depth > best_depth:
            best_depth = indent_depth
            best_parent = parent
    return best_parent


def get_orphan_goals(database):
    graph = nx.Graph()
    pending_goals = database.query(Goal).filter_by(
        state=GoalState.Pending).all()
    for goal in pending_goals:
        for parent in goal.parents:
            if parent.state != GoalState.Pending:
                continue
            graph.add_edge(goal.id, parent.id)
    orphan_goals = []
    roots = get_roots(pending_goals)
    for goal in pending_goals:
        if goal in roots:
            continue
        if goal.id not in graph:
            orphan_goals.append(goal)
        for root in roots:
            if root.id not in graph:
                continue
            if nx.has_path(graph, goal.id, root.id):
                break
        else:
            orphan_goals.append(goal)
    return orphan_goals


def format_goal_text(goals, zone, show_archived=False):
    roots = get_roots(goals)
    indent_depth = 0
    return '\n'.join(prepare_plan_lines(
        roots, zone, indent_depth, show_archived))


def format_schedule_text(goals, zone, show_archived=False):
    goals_by_date = defaultdict(list)
    remaining_goals = list(goals)
    while remaining_goals:
        g = remaining_goals.pop()
        remaining_goals.extend(g.children)
        if not show_archived and g.state != GoalState.Pending:
            continue
        utc_datetime = g.schedule_datetime
        if not utc_datetime:
            continue
        local_datetime = zone_datetime(utc_datetime, UTC_TIMEZONE, zone)
        selected_goals = goals_by_date[local_datetime.date()]
        if g not in selected_goals:
            selected_goals.append(g)
    lines = []
    for goal_date in sorted(goals_by_date.keys()):
        selected_goals = goals_by_date[goal_date]
        sorted_goals = sort_by_attribute(selected_goals, 'schedule_datetime')
        lines.append(goal_date.strftime(DATESTAMP_FORMAT))
        lines.extend([g.render_text(
            zone, indent_depth=1) for g in sorted_goals])
    return '\n'.join(lines)


def format_mission_text(goals, zone, show_archived=False):
    lines = []

    def prepare_section(section_name, section_text):
        lines.append('# %s' % section_name)
        if section_text:
            lines.append(section_text)
        lines.append('')

    goal_count = len(goals)
    if goal_count == 1:
        goal = goals[0]
        prepare_section('Mission', goal.render_text(zone))
        prepare_section('Log', format_log_text(goal.sorted_notes, zone))
        goals = goal.children
    prepare_section('Schedule', format_schedule_text(
        goals, zone, show_archived=show_archived))
    prepare_section('Tasks', '\n'.join(prepare_plan_lines(
        goals, zone, indent_depth=1, show_archived=show_archived)))
    return '\n'.join(lines)


def prepare_plan_lines(goals, zone, indent_depth, show_archived):
    lines = []
    for g in sort_by_attribute(get_roots(goals), 'order'):
        if not show_archived and g.state != GoalState.Pending:
            continue
        lines.append(g.render_text(zone, indent_depth))
        lines.extend(prepare_plan_lines(
            g.children, zone, indent_depth + 1, show_archived))
    return lines


def format_log_text(notes, zone):
    return '\n\n'.join(_.render_text(zone) for _ in notes)


def parse_goal_text(goal_cache, text, zone):
    goal_by_id = {}
    parent_by_indent_depth = {}
    order = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        goal = Goal.parse_text(goal_cache, line, zone)
        goal.order = order = order + 1
        goal_parent = get_parent(goal.indent_depth, parent_by_indent_depth)
        if not hasattr(goal, 'explicit_parents'):
            goal.explicit_parents = []
        if goal_parent:
            goal.explicit_parents.append(goal_parent)
        update_parent_by_indent_depth(
            goal, goal.indent_depth, parent_by_indent_depth)
        goal_by_id[goal.id] = goal
    for goal in goal_by_id.values():
        if not hasattr(goal, 'implicit_parents'):
            goal.implicit_parents = []
        for parent in goal.parents:
            if parent.id in goal_by_id:
                continue
            goal.implicit_parents.append(parent)
        goal.parents = goal.explicit_parents + goal.implicit_parents
    return goal_by_id.values()


def parse_schedule_text(goal_cache, text, zone):
    goals = []
    date = None
    for line in text.splitlines():
        line = line.strip()
        try:
            date = datetime.strptime(line, DATESTAMP_FORMAT)
        except ValueError:
            pass
        else:
            continue
        goal = Goal.parse_text(goal_cache, line, zone)
        goal.set_schedule_date(date, zone)
        goals.append(goal)
    return goals


def parse_mission_text(database, text, zone):
    goal_cache = GoalCache(database)
    text_by_key = parse_text_by_key(text, '# ', lambda line: line.lower())
    mission_text = text_by_key.get('mission', '')
    log_text = text_by_key.get('log', '')
    schedule_text = text_by_key.get('schedule', '')
    tasks_text = text_by_key.get('tasks', '')
    try:
        mission_goal = Goal.parse_text(
            goal_cache, mission_text.splitlines()[0], zone)
    except (KeyError, IndexError):
        mission_goal = None
    else:
        mission_goal.notes = parse_log_text(database, log_text, zone)
    goals = parse_goal_text(goal_cache, tasks_text, zone)
    goal_by_id = {_.id: _ for _ in goals}
    for g in parse_schedule_text(goal_cache, schedule_text, zone):
        try:
            goal = goal_by_id[g.id]
        except KeyError:
            g.order = len(goals)
            goals.append(g)
        else:
            goal.schedule_datetime = g.schedule_datetime
    if mission_goal:
        for g in goals:
            if not g.parents:
                g.parents.append(mission_goal)
        goals.append(mission_goal)
    return goals


def parse_log_text(database, text, zone):
    notes = []
    note_datetime = None
    note_id = None
    note_lines = []

    def process_note(note_id, note_datetime, note_lines):
        note_text = '\n'.join(note_lines).strip()
        note_lines.clear()
        if not note_text:
            return
        note = Note.get(database, note_id)
        if note_datetime:
            note.id_datetime = note_datetime
        note.set_text(note_text)
        notes.append(note)

    for line in text.splitlines():
        timestamp_text, _, id_text = line.partition(SEPARATOR)
        try:
            note_datetime = parse_timestamp(timestamp_text, zone)
            note_id = id_text.strip()
        except ValueError:
            note_lines.append(line)
            continue
        process_note(note_id, note_datetime, note_lines)
    process_note(note_id, note_datetime, note_lines)
    return notes


def update_parent_by_indent_depth(goal, goal_depth, parent_by_indent_depth):
    bad_depths = []
    for indent_depth, parent in parent_by_indent_depth.items():
        if indent_depth > goal_depth:
            bad_depths.append(indent_depth)
            continue
    for indent_depth in bad_depths:
        del parent_by_indent_depth[indent_depth]
    parent_by_indent_depth[goal_depth] = goal


def backup_database(target_folder, database, timezone, terms=None):
    goals = get_goals(database, terms, with_notes=True)
    text = format_mission_text(goals, timezone, show_archived=True)
    target_folder = make_folder(target_folder)
    target_name = ' '.join(terms) if terms else 'goals'
    target_path = join(target_folder, f'{target_name}.md')
    open(target_path, 'wt').write(text)
    for goal in goals:
        if not goal.notes:
            continue
        text = format_mission_text([goal], timezone, show_archived=True)
        target_name = goal.id
        target_path = join(target_folder, f'{target_name}.md')
        open(target_path, 'wt').write(text)


def format_summary(database, zone):
    lines = []
    orphan_goals = get_orphan_goals(database)
    if orphan_goals:
        lines.append('%s orphaned' % len(orphan_goals))
        lines.extend(g.render_text(zone, indent_depth=1) for g in orphan_goals)
    pending_count = database.query(Goal).filter_by(
        state=GoalState.Pending).count()
    lines.append('%s pending' % pending_count)
    return '\n'.join(lines)
