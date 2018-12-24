import pytz
from datetime import datetime
from invisibleroads_macros.disk import TemporaryStorage
from invisibleroads_macros.iterable import OrderedDefaultDict
from os.path import join
from subprocess import call


DATESTAMP_FORMAT = '%Y%m%d'
TIMESTAMP_FORMAT = DATESTAMP_FORMAT + '-%H%M'
TIMESTAMP_FORMATS = (DATESTAMP_FORMAT, TIMESTAMP_FORMAT)
UTC_TIMEZONE = pytz.UTC


def call_editor(editor_command, file_name, file_text):
    with TemporaryStorage() as (storage):
        text_path = join(storage.folder, file_name)
        with open(text_path, 'wt') as (text_file):
            text_file.write(file_text)
            text_file.flush()
            call(editor_command.split() + [text_path])
        with open(text_path, 'rt') as (text_file):
            file_text = text_file.read()
    return file_text.strip()


def zone_datetime(x, source_timezone, target_timezone):
    return (x.replace(tzinfo=source_timezone)).astimezone(target_timezone)


def format_timestamp(x, target_timezone, timestamp_format=TIMESTAMP_FORMAT):
    return zone_datetime(x, UTC_TIMEZONE, target_timezone).strftime(
        timestamp_format)


def parse_timestamp(
        text, source_timezone, timestamp_formats=TIMESTAMP_FORMATS):
    text = text.strip()
    for timestamp_format in timestamp_formats:
        try:
            x = datetime.strptime(text, timestamp_format)
        except ValueError:
            continue

        break
    else:
        raise ValueError

    return zone_datetime(x, source_timezone, UTC_TIMEZONE)


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


def sort_by_attribute(items, attribute_name):
    packs = [(getattr(_, attribute_name), _) for _ in items]
    return [_[1] for _ in sorted(packs, key=lambda _: _[0])]
