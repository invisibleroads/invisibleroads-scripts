from invisibleroads_scripts.macros import parse_text_by_key
from models import Goal


def parse_mission_text(text):
    goal_by_id = {}
    text_by_key = parse_text_by_key(text, '# ', lambda key: key.lower())
    mission_text = text_by_key.get('mission', '')
    try:
        line = mission_text.splitlines()[0]
    except IndexError:
        pass
    else:
        goal = Goal.parse_text(line)
        goal_by_id[goal.id] = goal
    return goal_by_id


def format_mission_text(goal_by_id, goal_id=None):
    lines = []

    def prepare_section(section_name, section_text):
        lines.append('# %s' % section_name)
        if section_text:
            lines.append(section_text)
        lines.append('')

    if goal_id:
        goal = goal_by_id[goal_id]
        prepare_section('Mission', goal.format_text())
    prepare_section('Log', '')
    prepare_section('Schedule', '')
    prepare_section('Tasks', '')
    return '\n'.join(lines)
