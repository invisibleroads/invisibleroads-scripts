import re
from collections import defaultdict
from datetime import datetime
from glob import glob
from invisibleroads_macros.disk import TemporaryStorage
from invisibleroads_macros.iterable import OrderedDefaultDict
from os import environ
from os.path import join
from subprocess import call


EDITOR_COMMAND = environ.get('EDITOR', 'vim')
DATE_FORMAT = '%Y%m%d'
ID_PATTERN = re.compile(r'\[(.*?)\]')


class MissionDocument(object):

    def __init__(self, mission_text):
        self._text_by_heading = parse_text_by_key(
            mission_text, '# ', lambda line: line.lower())

    def __getitem__(self, key):
        return self._text_by_heading[key]

    def __setitem__(self, key, value):
        self._text_by_heading[key] = value

    def render(self):
        lines = []
        for heading, text in self._text_by_heading.items():
            lines.append('# ' + heading.title())
            lines.append(text)
            lines.append('')
        return '\n'.join(lines)


def run(mission_text_paths):
    mission_texts = [open(_).read() for _ in mission_text_paths]
    mission_documents = [MissionDocument(_) for _ in mission_texts]

    lines_by_timestamp = defaultdict(list)
    pack_by_id = {}
    for mission_index, mission_document in enumerate(mission_documents):
        try:
            schedule_text = mission_document['schedule']
        except KeyError:
            continue
        line_index = 0
        text_by_timestamp = parse_text_by_key(
            schedule_text, '## ', parse_timestamp)
        for timestamp, text in text_by_timestamp.items():
            lines = []
            for line in text.splitlines():
                line_id = mission_index, line_index
                pack_by_id[line_id] = timestamp, line
                if not line:
                    continue
                lines.append(line + ' [%s:%s]' % line_id)
                line_index += 1
            lines_by_timestamp[timestamp].extend(lines)
    schedule_text = format_schedule_text(lines_by_timestamp)

    with TemporaryStorage() as storage:
        schedule_text_path = join(storage.folder, 'schedule.md')
        with open(schedule_text_path, 'wt') as schedule_text_file:
            schedule_text_file.write(schedule_text)
            schedule_text_file.flush()
            call([EDITOR_COMMAND, schedule_text_path])
        with open(schedule_text_path, 'rt') as schedule_text_file:
            schedule_text = schedule_text_file.read()

    text_by_timestamp = parse_text_by_key(
        schedule_text, '## ', parse_timestamp)

    for timestamp, text in text_by_timestamp.items():
        for line in text.splitlines():
            line_match = ID_PATTERN.search(line)
            if not line_match:
                continue
            line_id_text = line_match.group(1)
            mission_index_string, line_index_string = line_id_text.split(':')
            mission_index = int(mission_index_string)
            line_index = int(line_index_string)
            line_id = mission_index, line_index
            pack_by_id[line_id] = timestamp, ID_PATTERN.sub('', line).rstrip()

    packs_by_mission_index = defaultdict(list)
    for line_id, (timestamp, line) in pack_by_id.items():
        mission_index, line_index = line_id
        packs_by_mission_index[mission_index].append((
            timestamp, line_index, line))
    for mission_index, packs in packs_by_mission_index.items():
        mission_document = mission_documents[mission_index]
        lines_by_timestamp = defaultdict(list)
        for timestamp, line_index, line in sorted(packs, key=lambda _: _[1]):
            lines_by_timestamp[timestamp].append(line)
        mission_document['schedule'] = '\n' + format_schedule_text(
            lines_by_timestamp)

    for path, document in zip(mission_text_paths, mission_documents):
        open(path, 'wt').write(document.render())


def parse_text_by_key(text, key_prefix, parse_key):
    lines_by_key = OrderedDefaultDict(list)
    key = ''
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith(key_prefix):
            key = parse_key(line.lstrip(key_prefix))
            continue
        lines_by_key[key].append(line)
    return {key: '\n'.join(lines) for key, lines in lines_by_key.items()}


def parse_timestamp(line):
    return datetime.strptime(line, DATE_FORMAT)


def format_schedule_text(lines_by_timestamp):
    try:
        schedule_lines = lines_by_timestamp.pop('')
    except KeyError:
        schedule_lines = []
    for timestamp in sorted(lines_by_timestamp.keys()):
        lines = lines_by_timestamp[timestamp]
        schedule_lines.append('## ' + timestamp.strftime(DATE_FORMAT))
        schedule_lines.extend(lines)
        schedule_lines.append('')
    return '\n'.join(schedule_lines).strip()


if __name__ == '__main__':
    mission_text_paths = glob('*.md')
    run(mission_text_paths)
