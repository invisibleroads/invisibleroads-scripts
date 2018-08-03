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
        return '\n'.join(lines)

    def save(self, target_path):
        open(target_path, 'wt').write(self.render())
        return target_path


def run(mission_text_paths):
    mission_texts = [open(_).read() for _ in mission_text_paths]
    mission_documents = [MissionDocument(_) for _ in mission_texts]
    lines_by_date, pack_by_id = prepare_lines_by_date(mission_documents)
    schedule_text = call_editor('schedule.md', format_schedule_text(
        lines_by_date))
    text_by_date = parse_text_by_key(schedule_text, '## ', parse_date)
    pack_by_id = process_text_by_date(text_by_date, pack_by_id)
    mission_documents = update_mission_documents(mission_documents, pack_by_id)
    for path, document in zip(mission_text_paths, mission_documents):
        document.save(path)


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


def parse_date(line):
    return datetime.strptime(line, DATE_FORMAT)


def format_schedule_text(lines_by_date):
    try:
        schedule_lines = lines_by_date.pop('')
    except KeyError:
        schedule_lines = []
    for date in sorted(lines_by_date.keys()):
        lines = lines_by_date[date]
        schedule_lines.append('\n## ' + date.strftime(DATE_FORMAT) + '\n')
        schedule_lines.extend(lines)
    return '\n'.join(schedule_lines).strip()


def call_editor(file_name, file_text):
    with TemporaryStorage() as storage:
        text_path = join(storage.folder, file_name)
        with open(text_path, 'wt') as text_file:
            text_file.write(file_text)
            text_file.flush()
            call([EDITOR_COMMAND, text_path])
        with open(text_path, 'rt') as text_file:
            file_text = text_file.read()
    return file_text


def prepare_lines_by_date(mission_documents):
    lines_by_date = defaultdict(list)
    pack_by_id = {}
    for mission_index, mission_document in enumerate(mission_documents):
        try:
            schedule_text = mission_document['schedule']
        except KeyError:
            continue
        line_index = 0
        text_by_date = parse_text_by_key(
            schedule_text, '## ', parse_date)
        for date, text in text_by_date.items():
            lines = []
            for line in text.splitlines():
                line_id = mission_index, line_index
                pack_by_id[line_id] = date, line
                if not line:
                    continue
                lines.append(line + ' [%s:%s]' % line_id)
                line_index += 1
            lines_by_date[date].extend(lines)
    return lines_by_date, pack_by_id


def process_text_by_date(text_by_date, pack_by_id):
    for date, text in text_by_date.items():
        for line in text.splitlines():
            line_match = ID_PATTERN.search(line)
            if not line_match:
                continue
            line_id_text = line_match.group(1)
            mission_index_string, line_index_string = line_id_text.split(':')
            mission_index = int(mission_index_string)
            line_index = int(line_index_string)
            line_id = mission_index, line_index
            pack_by_id[line_id] = date, ID_PATTERN.sub('', line).rstrip()
    return pack_by_id


def update_mission_documents(mission_documents, pack_by_id):
    packs_by_mission_index = defaultdict(list)
    for line_id, (date, line) in pack_by_id.items():
        mission_index, line_index = line_id
        packs_by_mission_index[mission_index].append((
            date, line_index, line))
    for mission_index, packs in packs_by_mission_index.items():
        mission_document = mission_documents[mission_index]
        lines_by_date = defaultdict(list)
        for date, line_index, line in sorted(packs, key=lambda _: _[1]):
            lines_by_date[date].append(line)
        mission_document['schedule'] = '\n' + format_schedule_text(
            lines_by_date)
    return mission_documents


if __name__ == '__main__':
    mission_text_paths = glob('**/*.md', recursive=True)
    run(mission_text_paths)
