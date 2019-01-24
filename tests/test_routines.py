from conftest import MISSION_TEXTS
from models import Goal
from routines import format_mission_text, parse_mission_text


def test_parse_mission_text():
    assert parse_mission_text(MISSION_TEXTS[0]) == {}
    assert parse_mission_text(MISSION_TEXTS[1]) == {
        0: Goal(id=0, text='Do')}
    """
    assert parse_mission_text(MISSION_TEXTS[2]) == {
        'A': Goal(id='A', text='Do')}
    """


def test_format_mission_text():
    assert MISSION_TEXTS[0] == format_mission_text({})
    assert MISSION_TEXTS[2] == format_mission_text({
        'A': Goal(id='A', text='Do')}, goal_id='A')
