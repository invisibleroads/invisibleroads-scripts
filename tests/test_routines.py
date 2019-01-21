from conftest import BLANK_MISSION_TEXT
"""
from invisibleroads_scripts.routines import (
    format_mission_text, parse_mission_text)
"""


def parse_mission_text(text):
    return {}


def format_mission_text(goal_by_id, goal_id=None):
    lines = []

    def prepare_section(section_name, section_text):
        lines.append('# %s' % section_name)
        if section_text:
            lines.append(section_text)
        lines.append('')

    if goal_id:
        prepare_section('Mission', '')
    prepare_section('Log', '')
    prepare_section('Schedule', '')
    prepare_section('Tasks', '')
    return '\n'.join(lines)


"""
def test_mission_text():
    goal_by_id = parse_mission_text(FULL_MISSION_TEXT)
    mission_text = format_mission_text(goal_by_id)
    assert FULL_MISSION_TEXT == mission_text
"""


def test_parse_mission_text():
    assert parse_mission_text(BLANK_MISSION_TEXT) == {}
    assert parse_mission_text('# Mission\nDo') == {0: 'Do'}


def test_format_mission_text():
    assert BLANK_MISSION_TEXT == format_mission_text({})
    assert '# Mission\nDo  # A' == format_mission_text({'A': 'Do'})
