from argparse import ArgumentParser

from macros import call_editor
from models import Goal, db
from routines import format_mission_text, parse_mission_text, get_goals


if __name__ == '__main__':
    argument_parser = ArgumentParser()
    argument_parser.add_argument('--goal_id')
    args = argument_parser.parse_args()
    goal = Goal()
    goal_id = args.goal_id
    if goal_id:
        goals = get_goals([goal_id], with_notes=True)
        if goals:
            goal = goals[0]
    while True:
        mission_text = call_editor('goal.md', format_mission_text(goal))
        try:
            goals = parse_mission_text(mission_text)
        except ValueError:
            print('Mission required.')
        break
    for goal in goals:
        db.add(goal)
        db.commit()
