from os.path import dirname, join


FOLDER = dirname(__file__)
EXAMPLES_FOLDER = join(FOLDER, 'examples')


def load_text(file_name):
    return open(join(EXAMPLES_FOLDER, file_name)).read()


MISSION_TEXTS = [
    load_text('mission0.md'),
    load_text('mission1.md'),
    load_text('mission2.md'),
    load_text('missionX.md'),
]
