from conftest import MISSION_TEXTS
from models import Goal
from routines import format_mission_text, parse_mission_text


def test_parse_mission_text():
    assert parse_mission_text(MISSION_TEXTS[0]) == {}
    assert parse_mission_text(MISSION_TEXTS[1]) == {
        0: Goal(id=0, text='Do')}
    assert parse_mission_text(MISSION_TEXTS[2]) == {
        'A': Goal(id='A', text='Do')}
    """
    assert parse_mission_text(MISSION_TEXTS[3]) == {
        1: Goal(id=1, text='Exercise'),
        2: Goal(id=2, text='Do 10 pullups'),
        3: Goal(id='C', text='Sleep'),
    }
    """


def test_format_mission_text():
    assert MISSION_TEXTS[0] == format_mission_text({})
    assert MISSION_TEXTS[2] == format_mission_text({
        'A': Goal(id='A', text='Do')}, goal_id='A')
    """
    assert MISSION_TEXTS[4] == format_mission_text({
        'A': Goal(id='A', text='Exercise'),
        'B': Goal(id='B', text='Do 10 pullups', parent_id='A'),
        'C': Goal(id='C', text='Sleep'),
    })
    # Reconsider whether to allow many to many for goals
    """
