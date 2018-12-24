import time
from configparser import ConfigParser
from invisibleroads.scripts import Script

from .macros import call_editor
from .models import get_database_from_configuration
from .routines import (
    backup_database,
    format_mission_text,
    format_summary,
    get_goals,
    parse_mission_text)
from .settings import (
    get_archive_folder,
    get_editor_command,
    get_editor_timezone,
    get_folder_by_terms,
    CONFIGURATION_PATH)


class EditMissionScript(Script):

    def configure(self, argument_subparser):
        argument_subparser.add_argument(
            '--configuration_path', '-C', metavar='PATH',
            default=CONFIGURATION_PATH)
        argument_subparser.add_argument('--all', '-A', action='store_true')
        argument_subparser.add_argument('terms', nargs='*')

    def run(self, args):
        c = ConfigParser()
        c.read(args.configuration_path)
        editor_command = get_editor_command(c)
        timezone = get_editor_timezone(c)
        database = get_database_from_configuration(c)
        archive_folder = get_archive_folder(c)
        folder_by_terms = get_folder_by_terms(c)
        goals = get_goals(database, args.terms)
        # Edit
        while True:
            text = format_mission_text(goals, timezone, show_archived=args.all)
            text = call_editor(editor_command, 'mission.md', text)
            try:
                goals = parse_mission_text(text, timezone)
            except ValueError:
                print('Please specify a mission.')
                time.sleep(3)
            break
        # Commit
        for goal in goals:
            database.add(goal)
            database.commit()
        # Backup
        backup_database(archive_folder, database, timezone)
        for terms, folder in folder_by_terms.items():
            backup_database(folder, database, timezone, terms)
        print(format_summary(database, timezone))
