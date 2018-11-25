from invisibleroads_macros.disk import TemporaryStorage
from invisibleroads_macros.iterable import OrderedDefaultDict
from os import environ
from os.path import join
from subprocess import call


EDITOR_COMMAND = environ.get('EDITOR', 'vim')


def call_editor(file_name, file_text):
    with TemporaryStorage() as storage:
        text_path = join(storage.folder, file_name)
        with open(text_path, 'wt') as text_file:
            text_file.write(file_text)
            text_file.flush()
            call([EDITOR_COMMAND, text_path])
        with open(text_path, 'rt') as text_file:
            file_text = text_file.read()
    return file_text.strip()


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
