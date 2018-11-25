from collections import defaultdict
from invisibleroads_macros.timestamp import parse_timestamp, DATESTAMP_FORMAT
from sqlalchemy.orm import joinedload

from macros import parse_text_by_key
from models import Goal, GoalState, Note, db, SEPARATOR


def get_goals(goal_ids=None, with_notes=False):
    goal_query = db.query(Goal)
    if goal_ids:
        goal_query = goal_query.filter(Goal.id.in_(goal_ids))
    if with_notes:
        goal_query = goal_query.options(joinedload(Goal.notes))
    return goal_query.options(
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
    indent_depth = 0
    return '\n'.join(prepare_plan_lines(roots, indent_depth, show_archived))


def format_schedule_text(goals, show_archived=False):
    goals_by_date = defaultdict(list)
    remaining_goals = list(goals)
    while remaining_goals:
        g = remaining_goals.pop()
        remaining_goals.extend(g.children)
        goal_datetime = g.schedule_datetime
        if not goal_datetime:
            continue
        goals_by_date[goal_datetime.date()].append(g)
    lines = []
    for goal_date in sorted(goals_by_date.keys()):
        goals = goals_by_date[goal_date]
        lines.append(goal_date.strftime(DATESTAMP_FORMAT))
        lines.extend([g.render_text(indent_depth=1) for g in goals])
    return '\n'.join(lines)


def format_mission_text(goal):
    lines = []

    def prepare_section(section_name, section_text):
        lines.append('# %s' % section_name)
        if section_text:
            lines.append(section_text)
        lines.append('')

    prepare_section('Mission', goal.render_text())
    prepare_section('Log', format_log_text(goal.sorted_notes))
    prepare_section('Schedule', format_schedule_text(
        goal.children, show_archived=False))
    prepare_section('Tasks', '\n'.join(prepare_plan_lines(
        goal.children, indent_depth=1, show_archived=True)))
    return '\n'.join(lines)


def prepare_plan_lines(goals, indent_depth, show_archived):
    lines = []
    for g in goals:
        if not show_archived and g.state != GoalState.Pending:
            continue
        lines.append(g.render_text(indent_depth))
        lines.extend(prepare_plan_lines(
            g.sorted_children, indent_depth + 1, show_archived))
    return lines


def format_log_text(notes):
    return '\n\n'.join(_.render_text() for _ in notes)


def parse_goal_text(text):
    goals = []
    parent_by_indent_depth = {}
    order = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        goal = Goal.parse_text(line)
        goal.order = order = order + 1
        goal_parent = get_parent(goal.indent_depth, parent_by_indent_depth)
        if not hasattr(goal, 'explicit_parents'):
            goal.explicit_parents = []
        if goal_parent:
            goal.explicit_parents.append(goal_parent)
        update_parent_by_indent_depth(
            goal, goal.indent_depth, parent_by_indent_depth)
        goals.append(goal)
    goal_ids = [goal.id for goal in goals]
    for goal in goals:
        goal.implicit_parents = []
        for parent in goal.parents:
            if parent.id in goal_ids:
                continue
            goal.implicit_parents.append(parent)
        goal.parents = goal.explicit_parents + goal.implicit_parents
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
        goal = Goal.parse_text(line)
        goal_datetime = goal.schedule_datetime
        if goal_date:
            goal.schedule_datetime = goal_date.replace(
                hour=goal_datetime.hour, minute=goal_datetime.minute)
        goals.append(goal)
    return goals


def parse_mission_text(text):
    text_by_key = parse_text_by_key(text, '# ', lambda line: line.lower())
    try:
        goal = Goal.parse_text(text_by_key.get('mission', '').splitlines()[0])
    except (KeyError, IndexError):
        raise ValueError
    goal.notes = parse_log_text(text_by_key.get('log', ''))
    goals = parse_goal_text(text_by_key.get('tasks', ''))
    goal_by_id = {_.id: _ for _ in goals}
    for g in parse_schedule_text(text_by_key.get('schedule', '')):
        try:
            goal = goal_by_id[g.id]
        except KeyError:
            goals.append(goal)
        else:
            goal.schedule_datetime = g.schedule_datetime
    for g in goals:
        if not g.parents:
            g.parents.append(goal)
    return [goal] + goals


def parse_log_text(text):
    notes = []
    note_datetime = None
    note_id = None
    note_lines = []

    def process_note(note_id, note_datetime, note_lines):
        if not note_lines:
            return
        note = Note.get(note_id)
        if note_datetime:
            note.id_datetime = note_datetime
        note.set_text('\n'.join(note_lines))
        notes.append(note)
        note_lines.clear()

    for line in text.splitlines():
        timestamp_text, _, id_text = line.partition(SEPARATOR)
        try:
            note_datetime = parse_timestamp(timestamp_text)
            note_id = id_text.strip()
        except ValueError:
            note_lines.append(line)
            continue
        process_note(note_id, note_datetime, note_lines)
    process_note(note_id, note_datetime, note_lines)
    return notes


def get_parent(goal_depth, parent_by_indent_depth):
    best_depth = -1
    best_parent = None
    for indent_depth, parent in parent_by_indent_depth.items():
        if goal_depth > indent_depth and indent_depth > best_depth:
            best_depth = indent_depth
            best_parent = parent
    return best_parent


def update_parent_by_indent_depth(goal, goal_depth, parent_by_indent_depth):
    bad_depths = []
    for indent_depth, parent in parent_by_indent_depth.items():
        if indent_depth > goal_depth:
            bad_depths.append(indent_depth)
            continue
    for indent_depth in bad_depths:
        del parent_by_indent_depth[indent_depth]
    parent_by_indent_depth[goal_depth] = goal
